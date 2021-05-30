[![](https://img.shields.io/github/release/parlane/ha-melview-custom/all.svg?style=for-the-badge)](https://github.com/parlane/ha-melview-custom/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![](https://img.shields.io/github/license/parlane/ha-melview-custom?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/badge/MAINTAINER-%40parlane-red?style=for-the-badge)](https://github.com/parlane)
[![](https://img.shields.io/badge/COMMUNITY-FORUM-success?style=for-the-badge)](https://community.home-assistant.io)

# MELView HomeAssistant custom component
A full featured Homeassistant custom component to drive MELView ATA and ATW devices.

This custom component is based on the native Home Assistant [MELCloud component](https://github.com/home-assistant/core/tree/dev/homeassistant/components/melcloud) released with version 0.106 and on the same underlying [pymelview library](https://github.com/vilppuvuorinen/pymelview).

## Custom component additional features
I just added some features to the existing native components, waiting for the same features to be implemented:

1. Login password is stored in the registry during integration configuration. The access token is recreated every time the Home Assistant start and is not stored in the registry. Now you must also provide login language from a list of available options. The language should be the same that you normaly use for other MELView application (e.g. your phone app).

1. During integration configuration you can choose to not create additional sensors.

1. Added control for **Vertical and Horizontal Swing Modes** on ATA devices using default Swing features.

1. Added sensor to monitor WiFi signal.

1. Added binary sensor to monitor error state.

1. Added some attributes to the sensors to provide additional information (SerialNo, Unit Info, etc)

## Installation & configuration
You can install this component in two ways: via HACS or manually.

### Option A: Installing via HACS
If you have HACS, you must add this repository ("https://github.com/parlane/ha-melview-custom") to your Custom Repository selecting the Configuration Tab in the HACS page.
After this you can go in the Integration Tab and search the "MELView Custom" component to install it.

### Option B: Manually installation (custom_component)
1. Clone the git master branch.
1. Unzip/copy the melview_custom direcotry within the `custom_components` directory of your homeassistant installation.
The `custom_components` directory resides within your homeassistant configuration directory.
Usually, the configuration directory is within your home (`~/.homeassistant/`).
In other words, the configuration directory of homeassistant is where the configuration.yaml file is located.
After a correct installation, your configuration directory should look like the following.
    ```
    └── ...
    └── configuration.yaml
    └── secrects.yaml
    └── custom_components
        └── melview_custom
            └── __init__.py
            └── binary_sensor.py
            └── climate.py
            └── ...
    ```

    **Note**: if the custom_components directory does not exist, you need to create it.

### Component setup
Once the component has been installed, you need to configure it in order to make it work.
There are two ways of doing so:
- Using the web interface (Lovelace) [**recommended**]
- Manually editing the configuration.yaml file

#### Option A: Configuration using the web UI [recommended]
Simply add a new "integration" and look for "MELView Custom" among the proposed ones. Do not confuse with "MELView" that is the native one!

#### Option B: Configuration via editing configuration.yaml
Follow these steps only if the previous configuration method did not work for you.

1. Setup your MELView credentials. Edit/create the `secrets.yaml` file,
 which is located within the config directory as well. Add the following:

     ```
    melview_username: my_melview_email@domain.com
    melview_password: my_melview_password
    ```

    Where "my_melview_email@domain.com" is your MELView account email and "my_melview_password" is the associated password.

1. Enable the component by editing the configuration.yaml file (within the config directory as well).
Edit it by adding the following lines:
    ```
    melview_custom:
      username: !secret melview_username
      password: !secret melview_password
      language: my_melview_language
    ```

    Where "my_melview_language" is your MELView account language and can be one of the following (eg: EN):

        EN = English
        BG = Bulgarian
        CS = Czech
        DA = Danish
        DE = German
        ET = Estonian
        ES = Spanish
        FR = French
        HY = Armenian
        LV = Latvian
        LT = Lithuanian
        HU = Hungarian
        NL = Dutch
        NO = Norwegian
        PL = Polish
        PT = Portuguese
        RU = Russian
        FI = Finnish
        SV = Swedish
        IT = Italian
        UK = Ukrainian
        TR = Turkish
        EL = Greek
        HR = Croatian
        RO = Romanian
        SL = Slovenian

**Note!** In this case you do not need to replace "!secret melview_username" and "!secret melview_password".
Those are place holders that homeassistant automatically replaces by looking at the secrets.yaml file.

1. Reboot hpme assistant
1. Congrats! You're all set!
