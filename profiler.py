"""Lightweight harness for profiling executables"""

import argparse
import textwrap
import subprocess
import math
import csv
import os
import re
import numpy as np

class CLIInterface(object):

    def __init__ (self):
        
        self.args = None
        self.cli = None

        
    def parse_commandline(self):
        """Parses Command Line"""

        #Instantiate command line parser.
        self.command = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=textwrap.dedent('''
                                                            Exe Profiler Utility v0.1.
                                                            Author: James Kent. 
                                                            Institution: University of Cambridge, 2017.
                                                            Email: jck42@cam.ac.uk

                                                            It is NOT a performance profiling tool, it just provides a framework for measuring back
                                                            values outputted by stdout from an executable against parameters that are fed to the exe.
                                                            
                                                            It allows plotting different parameters of complicated functions. 
                                                            
                                                            YOU define the command line parameters, and everything to be tested. Its default
                                                            mode is to profile an executable on the command line.'''))
        
        #Add required arguments.
        self.command.add_argument('--filepath', required=True, metavar='F', help=
				 ('Executable file path to Profile.'))
        self.command.add_argument('--fixed_parameters', required=True, metavar='FP', help=
                                        ('Appends these to filepath above.'))
        self.command.add_argument('--positional_parameters', required=True, metavar='PP',
                                    help='The positional arguments of the executable.')
        self.command.add_argument('--variable_parameters', required=True, metavar='VP',
                                  type = lambda s: [item for item in s.split(',')],
                                    help='The parameter to vary.')
#        self.command.add_argument('--variable_parameters_values',  required=True, metavar='VPV', 
#                                    type = lambda s: [item for item in s.split(',')],
#                                    help='A list of parameters for each, e.g. var1,var2,var3,varx')
        self.command.add_argument('--easy_regex_output', required=False,metavar='ER',
                                    help='Searches for a number after this string. '
                                    'Use --regex-output for more robustness.')
        self.command.add_argument('--regex_output', required=False, metavar='R',
                                    help='Regular expression to identify the value of'
                                    ' interest in the stdout stream from executable.')
        self.command.add_argument('--output_csv_file', required=True, metavar='C',help='Saves to this CSV file.')

        #Optional arguements.
        self.command.add_argument('--echocommands',dest='echocommands',action='store_true',help='Echo Commands Back. Stops profiler from running. For debugging.')
        self.command.add_argument('--run_average',required=False ,default='3',help='How many times to run each param combination for averaging purposes.')
        
        #Parse the command line. 
        self.args = self.command.parse_args()

        #If in debug mode, echo everything back to user. Or instantiate profiler.
        if(self.args.echocommands is True):
            self._echo_commands()
    
    def _echo_commands(self):

        print("Received Arguments: \n")
        print(self.args)

class ExeProfiler(object):
    def __init__(self,args):

        self.args = args
        #print(self.args)
        print(self.args.fixed_parameters)
#        self.paramnames = self.args.variable_parameters_values
        self.var_param_list = []

    def _build_param_list(self):

        var_params = []
        cmd_list = []
        np_params = []
    
        for param in self.args.variable_parameters:

            print("\n Please configure parameter: {}".format(param))
            start_val = input("Start Value: ")
            end_val = input("End Value: ")
            inc_val = input("Increment: ")

            var_params.append((start_val,end_val,inc_val,param))

        if len(var_params) == 2:

            

            X = np.arange(int(var_params[0][0]),int(var_params[0][1]),int(var_params[0][2]))
            Y = np.arange(int(var_params[1][0]),int(var_params[1][1]),int(var_params[1][2]))
            np_params = [X,Y]
            X,Y = np.meshgrid(X,Y)

        
            print(X)
            print(Y)
            print(np_params)
            for X_i,Y_i in zip(X.flatten(),Y.flatten()):
                arg = "./{} {} {}={} {}={} {}".format(self.args.filepath,self.args.fixed_parameters,
                    var_params[0][3],str(X_i),var_params[1][3],str(Y_i), self.args.positional_parameters)
                print(arg)
                cmd_list.append(arg)
                
            
        elif len(var_params) > 2:
            raise AttributeError("More than two-dimensions of parameters detected. Not supported! (yet)")
        else:

            param = var_params[0]

            np_params = np.arange(float(param[0]),float(param[1]),float(param[2]))
            
            for var_param in np_params:
                arg = "./{} {} {}={} {}".format(self.args.filepath,self.args.fixed_parameters,
                        param[3],str(var_param), self.args.positional_parameters)
                print(arg)
                cmd_list.append(arg)

                
        print(cmd_list)
        return cmd_list, np_params

    def _execute_command(self,command): 
        #TODO: Implement error catching for seg fauls in executable etc.
        process = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE)
        process.wait()
        std_out,std_err = process.communicate()
        output_list = std_out.decode('utf8')
        
        return output_list

    def _grep_output(self, output_list):
        #TODO: make generic for any returned value. e.g. multiple values. 
        print(output_list)
        # Oh lord, bless this regex and make it strong lord, so it has the strength to persevere and never fail me.
        # For thine is the text block, string, and wild-card. Amen.
        if self.args.regex_output is not None:
            match = re.search(self.args.regex_output,output_list)
        elif self.args.easy_regex_output is not None:
            match = re.search("[\n\r].*"+self.args.easy_regex_output+"\s*(\d+\.\d+)",output_list)
        else:
            #Default regex, looks for a time output from script.
            #Reason I chose this as I designed this for profiling execution time of algorithms. 
            #Specify your own regex for other things!
            match = re.search("[\n\r].*Time:\s*(\d+\.\d+)",output_list)
        print(match)
        if match:
            print(match.group(1))
            return match.group(1)
        else:
            raise AttributeError("Regex expression found nothing!")
        return None

    def profile_exe(self):
        #TODO:  Make generic for multiple-parameters
        cmd_list,params = self._build_param_list()
        average_iter = int(self.args.run_average)
        outputs= None

        csv = CSVWriter(self.args.output_csv_file,['Param','Time'])

        #This is a bit hacky until I can generalise it to several parameters.
        if len(params) == 2:

#            print(params[0].size)
#            print(params[1].size)
            times_av = np.zeros((params[0].size,params[1].size))
            i = 0 #This is horrible but I can't think of another way :(
            for idx_x,xvar in enumerate(params[0]):
                for idx_y,yvar in enumerate(params[1]):
                    times = []
                    for run in range(0,average_iter):
                        output= self._execute_command(cmd_list[i])
                        if output:
                            time = float(self._grep_output(output))
                            times.append(time)
                    times_av[idx_x][idx_y] = (sum(times)/len(times))
                            
                    i+= 1

            times_av = np.insert(times_av, 0, params[0],axis=1)
            param1 = np.insert(params[1], 0, 0, axis=0)
            times_av = np.insert(times_av, 0, param1,axis=0)

            print(times_av)
            np.savetxt("output.csv",times_av)
            outputs = times_av
        else:
            times_av = []
            for command,varp in zip(cmd_list,params):
                times = []
                for run in range(0,average_iter):
                    output = self._execute_command(command)
                    if output:
                        time = float(self._grep_output(output))
                        times.append(time)
                        times_av.append(sum(times)/len(times))
                        csv.WriteRowtoFile(self.args.output_csv_file,[str(varp),str(sum(times)/len(times))])
                        outputs = list(zip(params,times_av))

                        
        return outputs



class CSVWriter(object):

    def __init__(self,filename,headers):
        
        self.filename = filename
        self.CreateCSVFile(self.filename,headers)


    def CreateCSVFile(self,filename,headers):

        
        #Opens CSV file ready for data to be appended. This allows performance data to be saved to the file as the script runs
        #instead of all data being written on completion. This means a crash for whatever reason will still yield some data!

        with open(filename,'w') as csvfile:
            perfwriter = csv.writer(csvfile,delimiter=',',quotechar='|',quoting=csv.QUOTE_MINIMAL)
            perfwriter.writerow(headers)
        print("\nCSV Data File Created: {}".format(filename))


    def WriteRowtoFile(sself,filename,data):

        print("Writing Row...")

        with open (filename,'a') as csvfile:
            perfwriter = csv.writer(csvfile,delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            perfwriter.writerow(data)

    def WritetoFile(self,filename,data):

        print("Writing to CSV File...") 
        #Writes performance data to CSV file. Opens file, instantiates csv writer, and writes data.
        with open (filename,'a') as csvfile:
            perfwriter = csv.writer(csvfile, delimiter=',',quotechar='|',quoting=csv.QUOTE_MINIMAL)
            # Write data 
            print("Data: {}".format(data))
            if type(data) is list:
                for item in data:
                    perfwriter.writerow(item)
                    print("Writing finished!")
            else: 
                print("List expected!!")


def main():

    cli = CLIInterface()
    cli.parse_commandline()
    prof = ExeProfiler(cli.args)
    outputs = prof.profile_exe()
    print(outputs)
    #csv = CSVWriter(cli.args.output_csv_file,[cli.args.variable_parameter,'Time'])
    #csv.WritetoFile(cli.args.output_csv_file,outputs)

if __name__=="__main__":
    main()
