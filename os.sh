#!/bin/bash
echo "0-100之间的质数有："
for ((i=2; i<=100; i++))
do
    flag=1
    for ((j=2; j*j<=i; j++))
    do
        if [ $((i % j)) -eq 0 ]
        then
            flag=0
            break
        fi
    done
    if [ $flag -eq 1 ]
    then
        echo -n "$i "
    fi
done
echo