# OCP 4 Utils
Util script to generate append-files for ignition configuration using [filetranspile](https://github.com/ashcrow/filetranspiler)

## Usage
Clone the repository
```bash
# git clone https://github.com/spagno/ocp4-utils.git && cd ocp4-utils
```
Configure the `URL_IGNITION_FILES` parameter in the config file
Prepare the servers.txt file (1 entry per line)
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1:::ens192::" > servers.txt
```
Or if you want to specify a hostname
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1:bootstrap.example.com:time.ien.it:ens192::" > servers.txt
```
Or if you want to specify a ntp server
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1::time.ien.it:ens192::" > servers.txt
```
Or if you want to specify different if_template
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1:::ens192:ifcfg-template-new:" > servers.txt
```
Or if you want to specify different append-template
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1:::ens192::append-template-new" > servers.txt
```
Or if you want to specify both
```bash
# echo "bootstrap:bootstrap:192.0.2.10:24:192.0.2.1:::ens192:ifcfg-template-new:append-template-new" > servers.txt
```
Run the script
```bash
# ./prepare.sh
```
The directory 'configFiles' will be created with the ignition files in plain text and base64
```bash
# ls configFiles
bootstrap.64  bootstrap.ign
```

### THANKS
Special thanks to Matteo Croce for the tips
