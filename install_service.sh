sudo cp mary_poppins.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/mary_poppins.service
sudo systemctl daemon-reload
sudo systemctl enable mary_poppins
sudo systemctl start mary_poppins
sudo systemctl status mary_poppins
