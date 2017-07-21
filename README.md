# Exe-Harness

This is supposed to be a lightweight harness for working on executables, for profiling values which are reported back
for a given combination of parameters. It is almost generic currently but there is work to be done.


## To run 

This will list all parameters:

```
python3 profiler.py --help
```

It works in the same way you specify command line arguments to functions. i.e

```
./mybinary.out positional_arg_1 --opt_arg=hello
```
The python program facilitates keeping all parameters fixed but one and then iterating over a set of values for a 
single given variable parameter.

You must specify:

* A filepath to an executable to profile.
* The positional arguements, in the correct order obviously.
* Any fixed parameters, e.g --debug=True
* The name of the parameter you want to vary.
* All values you want to test.
* Any other parameters, such as a custom regex expression for what you want to find. 

An example invocation would be:

```
python3 profiler.py /path/to/my/exe.out --fixed_parameters="--precision=5 --concat=1"  --variable_parameter=--iterations --variable_parameters_values=80,300,450,500,800 --output_csv_file=test.csv --positional_parameters=file.txt --run_average=1    
```

It will then run the executable, find each value specified by a regex expression (you can specify our own) and then it will save every parameter varation
and its output value to a csv file. 

## To do

I would like to:

* Make it more generic for the regex parsing, might be a string,number etc.
* Allow testing of multiple parameters, i.e more degrees of freedom. Doing this naively could be very costly.
* Would be cool to optimise a binary of n-parameters for time or something similar. Would require a proper state space exploration algorithm. Perhaps Bayesys?
