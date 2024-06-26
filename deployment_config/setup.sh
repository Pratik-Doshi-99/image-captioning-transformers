echo "________________________________________________________________________"
echo "Updting apt next..."
echo "________________________________________________________________________"
apt update

echo "________________________________________________________________________"
echo "Apt Updated"
echo "________________________________________________________________________"
echo "Installing vim next..."
echo "________________________________________________________________________"
apt install vim

echo "________________________________________________________________________"
echo "Vim Installed"
echo "________________________________________________________________________"
echo "Installing net-tools next..."
echo "________________________________________________________________________"
apt install net-tools

echo "________________________________________________________________________"
echo "Net tools installed"
echo "________________________________________________________________________"
echo "Installing python next..."
echo "________________________________________________________________________"
apt install python3

echo "________________________________________________________________________"
echo "Python Installed"
echo "________________________________________________________________________"
echo "Installing pip next..."
echo "________________________________________________________________________"
apt install python3-pip

echo "________________________________________________________________________"
echo "Pip installed"
echo "________________________________________________________________________"
echo "Installing libraries next..."
echo "________________________________________________________________________"
python3 -m pip install -r requirements.txt

echo "________________________________________________________________________"
echo "Python Libraries Installed"
echo "________________________________________________________________________"

echo "Done"