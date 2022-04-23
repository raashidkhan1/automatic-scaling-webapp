# automatic-scaling-webapp
Cloud Computing LAB assignment 1

Using the script (Not tested yet) -
Run
```
python controller --haproxy_stats_cmd "echo 'show stat' | nc -U /var/run/haproxy/haproxy.sock | grep 'backend-https,BACKEND'"
```
Initial setup Code-
1) controller.py - to run the monitoring and autoscaling
2) objst.py - provided web api for backend
3) haproxy.cfg - config for the haproxy needs to be updated in the container
4) data - folder to read/store objects from calling the web apis, which is essentially to mimic a web application.


Tasks remaining -
1) Use meaningful metrics from the haproxy stats, <Raashid>I stil need to figure out how to run both monitoring and auto-scaling indefinetly.
2) Auto-scaling using podman commands or podman rest APIs, helpful link to using API in python - https://www.nylas.com/blog/use-python-requests-module-rest-apis/
3) Need to figure out how to add container instances of webapp other than the load balancer itself running on a container.
3.1) Another part to logically implement threading to run both monitoring and auto scaling on different non-blocking threads.
4) Updating haproxy.cfg when starting/stopping containers of webapp instances.
5) testing the setup using locust - https://docs.locust.io/en/stable/quickstart.html