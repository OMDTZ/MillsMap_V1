# Tanzania Nationwide Mills Census - Webmap

This repo queries odk central server and updates a webmap automatically. Currently specific to a project in Tanzania funded by The World Food Programme (WFP) and conducted by OpenMap Development Tanzania (OMDTZ).

## Infrastructure set-up
The map is composed of two main components, which are 
- Data collection server (www.omdtz-data.org)
- Web-map  (www.millmaps.org)

### Requirements for deploying data collection server
For server deployment, you are needed to prepare the following 
- Domain name. In our case, we bought a domain from https://www.namecheap.com/
- Server for hosting, in our case we used https://cloud.digitalocean.com/ which cost $ 24 /month, and specification of 4GB of Ram / 2 CPUs, 80 GB SSD Disk 4 TB transfer. We also added the external 150GB SSD to support pictures and data hosting but for now we can aim for minimal specifications because we are not expecting a large amount of data to be uploaded.

### Requirements for deploying Web-map
For Web-map, you are needed to prepare the following 
- Domain name, because it uses let’s encrypt for the SSL, you should provide the domain in the very early stage. In our case, we bought a domain from https://www.namecheap.com/
- Server for hosting, in our case we used https://cloud.digitalocean.com/. With specifications of 1GB RAM / 1CPU and 25 GB SSD Disk. For the local infrastructure, you can create virtual machines.

### Steps for deploying Data collection server
- Creating new droplets
  - Creating an account in the digital ocean
  - Launch a droplet; At the very top, under Choose an image, switch to the Marketplace tab and select the Docker option. The docker version does not matter, and the system will run on ubuntu 20.04 or higher. 
  - Choose the size of droplets; basic, regular with SSD the smallest available option
  - Choose Authentication Method; for more security, we recommend ssh but you can also opt password
  - Rename and create the droplets.
![Alt text](/app/static/static_figures/doplets.png?raw=true "Title")

- Connecting Domain
  - Buy a domain from your provider eg www.millmaps.org
  - In digital ocean 
    - Right-click on the 3 dots after the droplets you created
![Alt text](/app/static/static_figures/domain.png?raw=true "Title")
    - Click add domain
      - Add the domain name you bought eg millmaps.org
      - Add CNAME as *
      - Copy all the name servers which are 
        - ns1.digitalocean.com. 
        - Ns2.digitalocean.com.
        - Ns3.digitalocean.com.
![Alt text](/app/static/static_figures/domain-ocean.png?raw=true "Title")
  - From Domain name service provides. I.e Namecheap
    - Click manage, on the right or the domain you just bought
    - Navigate to name servers, change the section to custom DNS then add all the nameservers copied from the digital ocean which are 
      - Ns1.digitalocean.com. 
      - Ns2.digitalocean.com.
      - Ns3.digitalocean.com.
![Alt text](/app/static/static_figures/Domain_digital ocean.png?raw=true "Title")
      
***The whole process above can take up to 24 hr to reflect***

- Installing Data collection server (ODK central)
  - From your terminal, ssh to the server; you can use the IP address provided and username as root. If the domain has already been reflected you can use it.
  - Start by updating and upgrading the OS 
  - Then upgrade the server
    ```
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
    ```
  - Start up the docker by run 
  ```
  systemctl enable docker
  ```
  - Modify system firewall by running
  ```
  ufw disable 
  ```
   and you it will prompt "Firewall stopped and disabled on system startup"
  - Download the application; 
  ```
  git clone https://github.com/getodk/central
  ```
  - Navigate to central directory by typing cd central
  - Add the missing components, and make sure you are in the central directory and paste the following; 
  ```
  git submodule update -i
  ```
  - Copy the template so as you can be able to edit it
  ```
   mv .env.template .env
  ```
  - The edit the file and add domain and emails as follows
    - Type nano .env the text editor will be launched and
      - #Use fully qualified domain names. Set to DOMAIN=local if SSL_TYPE=selfsign.
      DOMAIN=omdtz-data.org (added domain name)
      - #Used for Let's Encrypt expiration emails and Enketo technical support emails
      SYSADMIN_EMAIL=iddichazua6@gmail.com (added email)
      - #Options: letsencrypt, customssl, upstream, selfsign
      SSL_TYPE=letsencrypt
      - #Do not change if using SSL_TYPE=letsencrypt
      - HTTP_PORT=80
      - HTTPS_PORT=443
  ![Alt text](/app/static/static_figures/server.png?raw=true "Title")
    - Start installing the server by typing; 
    ```
    docker-compose build
    ```
    - Start the server; 
    ```
    docker-compose up -d
    ``` 
- Logging into the server and adding user
  - Ensure that you are in the central folder on your server. 
  - Adding users ( Substituting your email address as appropriate. Press Enter, and you will be asked for a password for this new account.)
  ```
  docker-compose exec service odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-create
  ```
  - Make the user as admin 
  ```
  docker-compose exec service odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-promote
  ```
  
  - You are done for now, but if you ever lose track of your password, you can always reset it by typing docker-compose exec service odk-cmd --email YOUREMAIL@ADDRESSHERE.com user-set-password. As with account creation, you will be prompted for a new password after you press Enter.

## For more information about server set up
- Set up Server, 
ODK central used and was deployed in Digital ocean by using the following procedures in this link https://docs.getodk.org/central-install-digital-ocean/ 
- Creating digital questionnaire, this was done by guidance from this link; https://xlsform.org/en/



## Web Map installation

### Cloud deployment
- Create a Digital Ocean droplet (or other server on whatever infrastructure you prefer), and associate a domain name with it. Either disable the UFW firewall or poke the appropriate holes in it for nginx and ssh.
- Create a user called ```millsmap``` with sudo privileges.
- From the ```millsmap``` user account, clone this repo. Step into it with ```cd MillsMap```.
- You'll need a file called ```secret_tokens.json``` that contains a keys "email" and "password" that contain the username and password for an ODK Central server containing your mill map data.
- Run the installation script with ```script/setup.sh```.
  - Follow instructions. It needs the domain name, and your email so that LetsEncrypt can inform you when your certificate is expiring.

### Local dev setup
For now, these instructions are specific to GNU/Linux. If you are working on Windows they definitely won't work, and on Mac they will require some tweaking.

- First install some Python infrastructure using your package manager. On Debian-derived distros such as Ubuntu, it'll look like this (if you're on another distro family, replace ```apt``` with the relevant package manager):

```
sudo apt install -y build-essential libssl-dev libffi-dev python3-setuptools python3-venv python3-dev
```

- Now create a VirtualEnv and populate it with the libraries needed for MillsMap:

```
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install flask
pip install flask-wtf
pip install requests
pip install pandas
pip install matplotlib
pip install uwsgi
```


- At this point you're still in the venv (to the left of your terminal prompt you'll see ```(venv)```). If you want to get out of it for some reason, type ```deactivate``` (presumably that's not what you want to do right now, you want to start developing). To launch the local dev server, type ```python wsgi.py```. That'll launch a local webserver serving the Millsmap application on port 5000. Open your browser and visit [localhost:5000](http://localhost:5000/), which should display the application.

Another way to get a solid test webserver running to look for errors is with ```uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app --enable-threads``` (with venv activated).

Note: It's convenient to develop from a local server. However, it can be deceptive; because there is almost no bandwidth constraint or delay between your server and client (both the Flask app and the browser are on the same computer), you will not notice problems that come from depending on fast communication between server and client. You may get a nasty surprise when you deploy to the cloud and find that things are unacceptably slow, perhaps even to the point of requests timing out so nothing works at all. There are lots of reasons to have a cloud instance that you can use to test while developing; this is only one of them!

## How to update the Map  - Using ODK
Make sure you're using the server linked with webmap during the webmap installation stage 
- Create the digital questionnaire
- Open ODK-Central server and upload the questionare. Supportive information https://docs.getodk.org/central-forms/
- In Mobile phone, install ODK from playstore then click configure with QR code then scan the provided QR Code from your server
- Set your identity; Open ODK >setting> user and device  identity>form metadata> type your user name, phone number and email address 
- Open Your ODK application and you will find 5 options
  - Fill blank form 
  - Edit saved form 
  - Send finalized form 
  - View sent form 
  - Delete saved form
- In “Fill blank form”, you will find the deployed form, select and fill the information. 
- NB Please make sure you turn on location, to do so go to setting on your android then turn on LOCATION.After that fill information. 
Then use the “Send finalized form” option, select all the forms and send them
#### For more detailed information, you can visit this site https://docs.getodk.org/getting-started/