import os, sys
import argparse
from datetime import datetime
import shutil, errno
import logging

f_log = "%s/log" % (os.path.expanduser('~'))
if os.path.exists(f_log) is False:
    os.makedirs(f_log)
file_log = "%s/%s.log" % (f_log, os.path.basename(__file__).rstrip('\.py'))

logging.basicConfig(filename=file_log, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.getLogger().addHandler(logging.StreamHandler())

def get_backup_fname(backup_dir, volume_name):
    return  "%s/%s-%s" % (backup_dir, volume_name, \
                          datetime.now().strftime('%Y-%m-%d-%H%M%S'))

def get_size_mb(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size/(1000*1000)

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            try:
                shutil.copytree(s, d, symlinks, ignore)
            except shutil.Error as e:
                logging.warning('Warning: Some directories not copied under %s.' % (s))
            except OSError as e:
                logging.warning('Warning: Some directories not copied under %s.' % (s))
        else:
            shutil.copy2(s, d)

def backup_volume(volume_dir, volume_name, backup_dir):
    src_dir = "%s/%s" % (volume_dir, volume_name)
    dst_dir = get_backup_fname(backup_dir, volume_name)
    logging.info("Backup %s to %s." % (src_dir, dst_dir))
    if os.path.exists(dst_dir) is False:
        os.makedirs(dst_dir)

    copytree(src_dir, dst_dir)

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--docker_volume_list', required=True, default=".*", \
                        help="The list of volumes to backup. Separated by comma", type=str)
    parser.add_argument('--volume_dir', required=False, default="/var/lib/docker/volumes", \
                        help="The directory of the docker volumes", type=str)
    parser.add_argument('--backup_dir', required=False, default="/data/backup", \
                        help="Where to store the backupsets", type=str)
    l = parser.parse_args()
    volume_dir = l.volume_dir
    backup_dir = l.backup_dir
    docker_volume_list = l.docker_volume_list

    if os.path.exists(backup_dir) is False:
        logging.warning("Warning: backup directory(%s) doesn't exist. Create it in advance." \
                        % (backup_dir))
        os.makedirs(backup_dir)

    for volume_name in docker_volume_list.split(','):
        backup_volume(volume_dir, volume_name, backup_dir)

    # list folder size
    logging.info("List folders under %s." % (backup_dir))
    logging.info("{0:70} {1}".format("Folder Name", "SIZE"))
    folder_list = os.listdir(backup_dir)
    folder_list.sort()
    for directory in folder_list:
        size_mb = get_size_mb("%s/%s" % (backup_dir, directory))
        logging.info("{0:70} {1}MB".format(directory, str("{:10.2f}".format(size_mb))))