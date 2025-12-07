# DIVUS D+ KNX Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/florianraffl/divus_dplus.svg?style=flat-square)](https://github.com/florianraffl/divus_dplus/releases)
[![License](https://img.shields.io/github/license/florianraffl/divus_dplus.svg?style=flat-square)](LICENSE)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)

Home Assistant integration for DIVUS D+ KNX systems, enabling control and monitoring of KNX devices through the DIVUS D+ gateway.

> **Warning**  
> This integration is not affiliated with DIVUS GmbH. The developers take no responsibility for anything that happens to your devices because of this integration.

![DIVUS D+ KNX](custom_components/divus_dplus/icon.png)

## Features

- **Climate Control**: Full climate entity support for heating/cooling zones
- **Lighting**: Control lights with dimming and switching capabilities
- **Covers**: Control shutters, blinds, and other cover devices
- **Switches**: Control various KNX switches
- **Sensors**: Monitor temperature and other sensor data from your KNX system
- **Room-based Organization**: Devices organized by rooms for easy management

## Installation

### HACS (Recommended)

1. [Install HACS](https://hacs.xyz/docs/setup/download) if you haven't already
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (three dots) → Custom repositories
   - Add `https://github.com/florianraffl/divus_dplus` as repository
   - Select "Integration" as category
3. Click "Install" on the DIVUS D+ KNX integration
4. Restart Home Assistant
5. Go to Settings → Devices & Services → Add Integration
6. Search for "DIVUS D+ KNX" and follow the configuration steps

### Manual Installation

1. Download the [latest release](https://github.com/florianraffl/divus_dplus/releases)
2. Extract the `custom_components` folder to your Home Assistant's config folder
   - The resulting folder structure should be `config/custom_components/divus_dplus`
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "DIVUS D+ KNX" and configure your connection

## Configuration

During setup, you will need to provide:

- **Host**: IP address or hostname of your DIVUS D+ gateway
- **Username**: Your DIVUS D+ username
- **Password**: Your DIVUS D+ password

## Supported Entities

The integration creates the following entity types based on your KNX configuration:

### Climate Entities
- Display current and target temperature
- Target temperature setting

### Light Entities
- Dimmable lights with brightness control
- On/off switches for lighting

### Cover Entities
- Shutter and blind controls
- Position control
- Open/close/stop commands
- Support for both individual devices and room groups

### Switch Entities
- General KNX switch controls
- On/off functionality

### Sensor Entities
- Current temperature sensors
- Additional sensor data from KNX devices

## Known Issues

### Lack of Test Data for Different DIVUS D+ Configurations

Your DIVUS D+ setup might differ from the tested configurations. If you encounter issues or missing entities, please enable debug logging (see below) and create an issue with the debug information.

## Debugging

To enable debug logging for troubleshooting, add this to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.divus_dplus: debug
```

After enabling debug logging, reproduce the issue and check your Home Assistant logs for detailed information.

## Contributing

Contributions are welcome! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Reporting Issues

When reporting issues, please include:

- Home Assistant version
- Integration version
- DIVUS D+ gateway model and firmware version
- Debug logs (see Debugging section above)
- Steps to reproduce the issue

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Home Assistant community
- Built with the Home Assistant integration framework

## Support

- [Report Issues](https://github.com/florianraffl/divus_dplus/issues)
- [Discussion](https://github.com/florianraffl/divus_dplus/discussions)
