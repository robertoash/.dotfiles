#!/bin/bash

export PYTHONPATH=$PYTHONPATH:/home/rash/.config/scripts
/usr/bin/python3 /home/rash/.config/scripts/backup/snapshot_storage.py -s "backup_$(date +%Y%m%d_%H%M)"