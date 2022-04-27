from podman import PodmanClient
from subprocess import Popen
import subprocess
#------
import os
import tarfile



client = PodmanClient(base_url="unix:///run/podman/podman.sock")
c = client.containers.get("test")
help(client.containers)
c.stop()
c.wait()
arr = []
client.containers.run('cont2image',detach=True,auto_remove=True,name="myhaproxy")
client.containers.run()
client.containers.run("testcontainer",detach=True,)
client.containers.create("testcontainer",None,)
client.containers.create()
#if c.status == 'running':
# print(c.attrs['NetworkSettings']['Networks']['podman']['IPAddress'])
l = [c.name for c in client.containers.list()]
c = client.containers.get("testcontainer")
#if c.status == 'running':
# print(c.attrs['NetworkSettings']['Networks']['podman']['IPAddress'])
c.stop()


#--------------------------------------------- run HAproxy
client.containers.run('cont2image',detach=True,auto_remove=True,name="myhaproxy")
#
#for container in client.containers.list(all=True, filters={"name":"star_with_"}):     instead of name ancestor for image


#--------------------------------------------- run webserver container
code_mount = Mount(
    source=str(repo_root.absolute()),
    target=target_dir,
    type='bind',
)

client.containers.run('testcontainer',detach=True,auto_remove=True,name="mycontainer",mounts=[Mount(str('/objects'), str('srv/objects'), type="bind")])


#-------------------------------------------- list  running containers IP
from podman import PodmanClient
client = PodmanClient(base_url="unix:///run/podman/podman.sock")
for c in client.containers.list():
  c = client.containers.get(c.name)
  if c.status == 'running':
   print(c.attrs['NetworkSettings']['Networks']['podman']['IPAddress'])
#-------------------------------------------------------------- list running containers ip in an image
from podman import PodmanClient
client = PodmanClient(base_url="unix:///run/podman/podman.sock")
for c in client.containers.list(filters={'ancestor':''}):
  c = client.containers.get(c.name)
  print(c.image)
  if c.image == "localhost/cont2image":
    if c.status == 'running':
        print(c.attrs['NetworkSettings']['Networks']['podman']['IPAddress'])


#-------------------------------------------------------- run webserver image with mounting
command='''podman run -v /srv/objects:/objects  --rm -d --name mycontainer testcontainer'''

process=Popen(command,shell=True,stdout=subprocess.PIPE)
result=process.communicate()
print(result)

#-------------------------------------------------------- run webserver image with mounting API   Final
client.containers.run('testcontainer',detach=True,auto_remove=True,name="mycontainer",volumes={'objecttt':{'bind':"/objects"}})  # objecttt is the host directory


#-------------------------------------------------------- list running containers ip in an image to update haproxy.conf  Final
for c in client.containers.list(filters={'ancestor':'testcontainer'}):   #all = true for both running and non running
 x = client.containers.get(c.name)
 print(c.image)
 if x.status == 'running':
    print(x.attrs['NetworkSettings']['Networks']['podman']['IPAddress'])
     # IPcont = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']

#---------------------------------------------------------- stop container  Final and take the ip to delete from haproxy.conf
for c in client.containers.list(filters={'ancestor':'testcontainer'}):
 x = client.containers.get(c.name)
print (x)
if x.status == "running":
    x.stop()
    IPcont = x.attrs['NetworkSettings']['Networks']['podman']['IPAddress']
    print("container", x , "has stopped" , 'with IP addres', IPcont)
#----------------------------------------------------------------------------------------- copy file first try

command='''podman cp foozi.txt myhaproxy:/etc/haproxy/foozi.txt'''

process=Popen(command,shell=True,stdout=subprocess.PIPE)
result=process.communicate()
print(result)

#------------------------------------------------------------------------ copy file 2nd try


def copy_to(src, dst):
    name, dst = dst.split(':')
    container = client.containers.get(name)
    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()

    data = open(src + '.tar', 'rb').read()
    container.put_archive(os.path.dirname(dst), data)
# usage copy_to('/local/foo.txt', 'my-container:/tmp/foo.txt')

