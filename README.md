# nestibo
Nest Sensibo Integration

Control my Fujitsu heatpumps with Nest thermostats via Sensibo devices. Very early stages. Basically just hacking away to prove out some basic functionality. The code reeks of unused and inefficient stanzas. I'll clean that up later

Current Features:
- Changes heatpump to whatever temp I set my Nest to

Required Packages: 
- https://github.com/Sensibo/sensibo-python-sdk'
- https://github.com/jkoelker/python-nest'

Required Hardware:
- Sensibo Sky IR controller - https://sensibo.com/
- Nest Thermostat (testing on the E model, but other should work fine) - https://nest.com/thermostats/nest-thermostat-e/overview/
- IR based heating/cool devices. I have Fujitsu Halycon Heat Pumps

Hardware Config:
- Nest - I used a 24v converter attached to 110v power and bridged the heat/cool jumper on the thermostat. This tricks the nest into thinking I have heating and cooling attached to it. Essentially i just need to be able to pull data via the API, but Nest doesn't allow a way to spoof heat/cool sources within software so needed a hardware based hack
