#/bin/bash
pip install -e .
sudo systemctl restart jupyter.service
echo "C'est tout."