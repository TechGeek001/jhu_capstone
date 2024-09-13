# Set up Development Environment
Tested with Ubuntu 24.04

## References
https://github.com/jhu-information-security-institute/infrastructure/wiki/Docker-On-Ubuntu

## Instructions
Install Dependencies
```
sudo apt install ca-certificates curl -y
```
Add Docker's GPG key
```
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```
Add the required repository
```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
Run the following commands
```
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```
Log out and log back in again, then run and test Docker
```
sudo systemctl start docker
sudo systemctl enable docker
docker run hello-world
```