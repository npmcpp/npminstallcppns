## Run npm command and fix C++ namespaces in node_modules


Run npm command and post-process newly-installed C++ files.

Usage: 

    npmcmdcppns.py <args>
    
where `<args>` are arguments you would pass to npm. 

npmcmdcppns will call `npm <args>`, and then, if npm did not return an error,
and the first argument was either `install` or `upgrade`, it will scan the newly-installed node_modules
for C++ source and header files, and decorate the namespaces, to avoid conflicts.


Since you'll be running `npmcmdcppns` from your C++ project directory, either place 
the script on `PATH`, or create an alias for it, e.g.

`npmcmdcppns='python /path/to/npminstallcppns/npmcmdcppns.py'`

then use `npmcmdcppns` instead of `npm`.
