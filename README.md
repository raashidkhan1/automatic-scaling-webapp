# automatic-scaling-webapp
Cloud Computing LAB assignment 1

Using the script (Not tested yet) -
Run instructions in the controller file
Initial setup Code-
1) controller.py - to run the monitoring and autoscaling
2) objst.py - provided web api for backend
3) haproxy.cfg - config for the haproxy needs to be updated in the container
4) data - folder to read/store objects from calling the web apis, which is essentially to mimic a web application.
5) locustfile.py  - load generator


Tasks remaining -
1) Use meaningful metrics from the haproxy stats
2) Auto-scaling using podman commands or podman rest APIs, helpful link to using API in python - https://www.nylas.com/blog/use-python-requests-module-rest-apis/
3) Updating haproxy.cfg and reload haproxy when starting/stopping containers of webapp instances.
4) testing the setup using locust - https://docs.locust.io/en/stable/quickstart.html
