#!/bin/bash
source ./config
ORIGINAL_TEMPLATE=$TEMPLATE
ORIGINAL_IF_TEMPLATE=$INTERFACE_TEMPLATE
if [ -e configFiles ]; then
  rm -fr configFiles
fi
mkdir -p configFiles
if [ ! -e filetranspile ]; then
  wget $FILE_TRANSPILE -O ./filetranspile
  chmod +x ./filetranspile
fi
IFS=:
while read serverType server ip prefix gateway dns ntp interface if_template template
do
  TEMPLATE=${ORIGINAL_TEMPLATE}
  INTERFACE_TEMPLATE=${ORIGINAL_IF_TEMPLATE}
  mkdir -p fake-root-${server}/etc/sysconfig/network-scripts
  if [ ! -z $if_template ]; then
    INTERFACE_TEMPLATE="$if_template"
  fi
  if [ ! -z $template ]; then
    TEMPLATE="$template"
  fi
  sed -e "s/IP_ADDRESS/${ip}/g" \
      -e "s/INTERFACE/${interface}/g" \
      -e "s/GW/${gateway}/g" \
      -e "s/NET_PREFIX/${prefix}/g" $INTERFACE_TEMPLATE > fake-root-${server}/etc/sysconfig/network-scripts/ifcfg-${interface}
  
  DNS_NUMBER=1
  IFS=,
  for DNS in ${dns}
  do
    echo DNS${DNS_NUMBER}=${DNS} >> fake-root-${server}/etc/sysconfig/network-scripts/ifcfg-${interface} 
    DNS_NUMBER=$(( DNS_NUMBER + 1 ))
  done
  IFS=:
  cp ${TEMPLATE} configFiles/${server}.ign.tmp
  sed -e "s/PH_IP/${base64Net}/g" \
      -e "s/TYPE/${serverType}/g" \
      -e "s|URL_IGNITION_FILES|${URL_IGNITION_FILES}|g" \
      -i configFiles/${server}.ign.tmp
  if [ ! -z $ntp ]; then
    cp $NTP_TEMPLATE ./fake-root-${server}/etc/chrony.conf
    sed -e "s/NTP_SERVER/${ntp}/g" -i ./fake-root-${server}/etc/chrony.conf
  fi
  ./filetranspile -i configFiles/${server}.ign.tmp -f ./fake-root-${server} > configFiles/${server}.ign
  base64 -w0 configFiles/${server}.ign > configFiles/${server}.64
  rm -fr configFiles/${server}.ign.tmp
done < ${MAP_FILE}
rm -fr fake-root*
