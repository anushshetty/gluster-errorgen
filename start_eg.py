import os
import string
import sys
import commands
import time
import datetime

def clean_up_gluster_processes():
   (status, output) = commands.getstatusoutput("umount /mnt/nfs; umount /mnt/gluster; killall glusterfs; killall glusterfsd; killall glusterd; rm -rf /etc/glusterd")
   if status == 0:
        print "Cleaning up old gluster processes"

def edit_eg_volumes(vol_args,brick_count):    
   (status, output) = commands.getstatusoutput("./edit_eg_vol " + vol_args)
   if status == 0:
        print "Generated error-gen vol files"
   (status, output) = commands.getstatusoutput("kill -9 $(cat /etc/glusterd/nfs/run/nfs.pid)");
   if status == 0:
        print "Stopping NFS server"

def edit_server_volumes(vol_args,brick_count):
   (status, output) = commands.getstatusoutput("./edit_eg_vol " + vol_args + " " + str(brick_count))
   print output
   if status == 0:
        print "Added error-gen to server volume files"

def create_volume(gfs_path,vol_type,vol_type_count,brick_count):
    hostname=os.uname()[1]
    gfs_path_glusterd = gfs_path + "/sbin/glusterd"
    gfs_path_gluster = gfs_path + "/sbin/gluster"
    (status, output) = commands.getstatusoutput(gfs_path_glusterd)
    if status == 0:
        print "Starting glusterd on brick"
    out_str = ''
    for num in range(brick_count):
        out_str += " " + hostname +":/mnt/s"+ str(num)
    (status, output) = commands.getstatusoutput(gfs_path_gluster + " volume create eg_vol " + vol_type + " "  + vol_type_count + " "  +  out_str)
    if status == 0:
        print "Creating volumes on brick"

def start_volume(gfs_path):
    hostname=os.uname()[1]
    gfs_path_glusterfs = gfs_path + "/sbin/glusterfs"
    gfs_path_gluster = gfs_path + "/sbin/gluster"
    (status, output) = commands.getstatusoutput(gfs_path_gluster + " volume start eg_vol")
    if status == 0:
        print "Started volume"
    (status, output) = commands.getstatusoutput("mkdir -p /mnt/gluster")
    if status <> 0:
        print "Unable to create a directory /mnt/gluster"

def start_fuse_nfs(gfs_path):
    hostname=os.uname()[1]
    gfs_path_glusterfs = gfs_path + "/sbin/glusterfs"
    gfs_path_gluster = gfs_path + "/sbin/gluster"
    (status, output) = commands.getstatusoutput("mkdir -p /mnt/gluster")
    if status <> 0:
        print "Unable to create a directory /mnt/gluster"
    (status, output) = commands.getstatusoutput("mkdir -p /mnt/nfs")
    if status <> 0:
        print "Unable to create a directory /mnt/nfs"
    (status, output) = commands.getstatusoutput("modprobe fuse")
    (status, output) = commands.getstatusoutput(gfs_path_glusterfs + " -s " + hostname + " -l /gfs-fuse.log --volfile-id=eg_vol /mnt/gluster")
    if status <> 0:
       print "Starting fuse client failed"
    else:
       print "Started fuse client"
    (status, output) = commands.getstatusoutput(gfs_path_glusterfs + " -f /etc/glusterd/nfs/nfs-server.vol -p /etc/glusterd/nfs/run/nfs.pid -l /gluster/git/var/log/glusterfs/nfs.log")
    if status <> 0:
       print "Restarting NFS Server failed"
    else:
       print "Restarted NFS Server"
    (status, output) = commands.getstatusoutput("mount " + hostname + ":/eg_vol /mnt/nfs")
    if status <> 0:
       print "Mounting NFS client failed"
    else:
       print "Mounting NFS Server"

if __name__ == "__main__":
    if "-p" not in sys.argv:
        print "Must provide path to the glusterfs binary path. Eg. /opt/glusterfs/"    
        sys.exit(0)
    else:
        gfs_path = sys.argv[sys.argv.index("-p") + 1]


    if "-t" in sys.argv:
         vol_type = sys.argv[sys.argv.index("-t") + 1]
         if "-c" in sys.argv:                                                                                                                               
            vol_type_count = sys.argv[sys.argv.index("-c") + 1]                                                                                            
         else:                                                                                                                                              
            print "Please specify your " + vol_type + " count"
            vol_type_count=''
            sys.exit(0)
    else:
         vol_type = ''
         vol_type_count=''


    if "-b" in sys.argv:
         brick_count = sys.argv[sys.argv.index("-b") + 1]
    else:
         brick_count =1
    
    if vol_type_count > 1:
       if int(brick_count) == 1:
          print "The brick count has be greater than 1"
          sys.exit(0)
         
    if "-v" not in sys.argv:
        print "Must provide the translator name below which you'd like to add error-gen"
        sys.exit(0)
    else:
        egtrans = sys.argv[sys.argv.index("-v") + 1]
        vol_args = "eg_vol-" + egtrans

    if "-f" not in sys.argv:
        failure_count='5'
    else:
        failure_count = sys.argv[sys.argv.index("-f") + 1]
    
    if "-e" not in sys.argv:
        error_no=''
    else:
        error_no = sys.argv[sys.argv.index("-e")+  1]

    file1=open('EG_VOL','w')
    file1.writelines("volume eg\n")
    file1.writelines("    type debug/error-gen\n")
    file1.writelines("    option failure " + failure_count + "\n")
    if error_no != '':
       file1.writelines("    option error-no " + error_no + "\n")
    file1.writelines("    subvolumes tmp1\n")
    file1.writelines("end-volume\n\n")
    file1.writelines("volume " + vol_args + "\n")
    file1.close()

    brick_count=int(brick_count)
    clean_up_gluster_processes()
    create_volume(gfs_path,vol_type,vol_type_count,brick_count)
    edit_server_volumes(vol_args,brick_count)
    start_volume(gfs_path)
    edit_eg_volumes(vol_args,brick_count)
    start_fuse_nfs(gfs_path)
