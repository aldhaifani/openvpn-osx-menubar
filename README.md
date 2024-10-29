<h3 align="center">OpenVpn OSX MenuBar</h3>
<p align="center">
    A simple Python script that displays your OpenVpn IP in the macOS menu bar.
</p>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-script">About the Script</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->

## About the Project

This Python script uses the openvpn command to connect to a VPN and extracts the assigned IP address from the output. It then displays the IP address in the macOS menu bar using the rumps library.
The script supports the following features:
- Connects to the VPN using a provided configuration file (.ovpn)
- Continuously monitors the VPN connection and updates the menu bar with the current IP address
- Provides a "Quit" option in the menu to terminate the VPN connection

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Bootstrap][Python.org]][Python-url]

- `rumps` - A library makes developing apps for the macOS menu bar easy using Python.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->

## Getting Started

### Prerequisites

This script is built with Python and requires a Python interpreter to run. You can install Python from the official website: [Python.org](https://python.org)


This script also requires that you have openvpn installed in your system and can be accessed from the terminal. You can install openvpn using the following command:
```sh
brew install openvpn
```

### Installation & Usage

To install this script you 
1. Navigate to the directory where you want to install the script, to go to the home directory, run the following command:
   ```sh
   cd ~
   ```
2. Clone the repo
   ```sh
   git clone https://github.com/aldhaifani/openvpn-osx-menubar.git
   cd openvpn-osx-menubar
   ```
3. Install required packages
   ```sh
   pip install -r requirements.txt
   ```
4. Finally, run the script
   ```sh
   python main.py file.ovpn
   ```

*This should be enough for the script to work. However, you can setup an alias to run the script from anywhere in the terminal. To do this, add the following line to your `.bashrc` or `.zshrc` file:
```sh
# openvpn-osx-menubar alias
alias vpn="python ~/openvpn-osx-menubar/main.py"
```

After adding the alias, you can run the script from anywhere in the terminal by running the following command:
```sh
vpn file.ovpn
```


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE, which allows for open-source distribution and modification. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->

## Contact

Tareq - [@0x6ar8](https://x.com/0x6ar8) - me@tareq.live

<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Python.org]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://python.org

