<h3 align="center">OpenVPN OSX MenuBar</h3>
<p align="center">
    A lightweight menubar app that shows your OpenVPN connection status and IP address on macOS
    <br />
    <img src="https://img.shields.io/badge/python-3.6+-blue">
    <img src="https://img.shields.io/badge/platform-macOS-lightgrey">
</p>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#features">Features</a></li>
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
    <li><a href="#logging">Logging</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



## About The Project

A Python utility that integrates OpenVPN into your macOS menu bar, providing easy access to your VPN connection status and IP address.

### Features

- VPN IP display in menu bar
- Quick disconnect functionality
- Detailed logging system
- Custom log file support

### Built With

[![Python][Python.org]][Python-url]
- `rumps` - macOS menu bar integration
- `openvpn` - VPN client

<p align="right">(<a href="#readme-top">back to top</a>)</p>




<!-- GETTING STARTED -->

## Getting Started

### Prerequisites

- Python 3.6+
- OpenVPN: `brew install openvpn`

### Installation

1. Clone and enter directory:
   ```sh
   git clone https://github.com/aldhaifani/openvpn-osx-menubar.git
   cd openvpn-osx-menubar
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

Basic connection:
```sh
sudo python main.py config.ovpn
```

With custom log file:
```sh
sudo python main.py config.ovpn --log-file ~/custom/path/vpn.log
```

Optional: Add to `.zshrc`:
```sh
alias vpn="sudo python ~/openvpn-osx-menubar/main.py"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Logging

The application maintains detailed logs of all operations. By default, logs are written to `/tmp/ovpn_debug.log`, but you can specify a custom location using the `--log-file` argument.

Monitor logs in real-time:
```sh
tail -f /tmp/ovpn_debug.log
```

Logs include:
- Connection events
- IP address assignments
- Error messages
- Application start/stop events

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

