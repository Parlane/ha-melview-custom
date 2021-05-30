"""Constants for the MELView Climate integration."""

DOMAIN = "melview_custom"
MEL_DEVICES = "mel_devices"

CONF_LANGUAGE = "language"
CONF_DISABLE_SENSORS = "disable_sensors"

ATTR_STATUS = "status"
ATTR_VANE_VERTICAL = "vane_vertical"
ATTR_VANE_HORIZONTAL = "vane_horizontal"


class HorSwingModes:
    """Horizontal swing modes names."""

    Auto = "HorizontalAuto"
    Left = "HorizontalLeft"
    MiddleLeft = "HorizontalMiddleLeft"
    Middle = "HorizontalMiddle"
    MiddleRight = "HorizontalMiddleRight"
    Right = "HorizontalRight"
    Split = "HorizontalSplit"
    Swing = "HorizontalSwing"


class VertSwingModes:
    """Vertical swing modes names."""

    Auto = "VerticalAuto"
    Top = "VerticalTop"
    MiddleTop = "VerticalMiddleTop"
    Middle = "VerticalMiddle"
    MiddleBottom = "VerticalMiddleBottom"
    Bottom = "VerticalBottom"
    Swing = "VerticalSwing"


class Language:
    """Melview languages."""

    English = 0


LANGUAGES = {
    'EN': Language.English,
}
