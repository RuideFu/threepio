"""A slider with two handles, for picking a low/high pair on one track."""

from PySide6 import QtCore, QtGui, QtWidgets

# Qt's own sizeHint constants for sliders (qslider.cpp).
SLIDER_LENGTH = 84
TICK_SPACE = 5

# Thickness of the painted selection bar, matching the groove height the
# stylesheet gives the plain sliders next to us.
BAND_HEIGHT = 4


class RangeSlider(QtWidgets.QWidget):
    """Horizontal slider whose low and high handles bound a selected range.

    Qt ships no range slider, so this paints two handles on one groove by
    asking the platform style to draw them: the handles, ticks, and focus ring
    then match the plain QSliders beside it in either color theme.

    Drag a handle to move that end, or the bar between them to slide the whole
    window; the handles stop `minimumSpan` apart so the range never collapses.
    """

    valuesChanged = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 100
        self._low = 0
        self._high = 100
        self._minimum_span = 0
        self._single_step = 1
        self._page_step = 10
        self._tick_interval = 0

        # Which handle the mouse or keyboard is working on: "low", "high",
        # "band" (both at once), or None while nothing is pressed.
        self._pressed = None
        self._active = "high"
        self._grab_value = 0
        self._grab_low = 0
        self._grab_high = 0

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

    # ---------------------------------------------------------------- values

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def setRange(self, minimum: int, maximum: int):
        self._minimum = int(minimum)
        self._maximum = max(int(maximum), self._minimum)
        self.setValues(self._low, self._high)

    def low(self) -> int:
        return self._low

    def high(self) -> int:
        return self._high

    def values(self) -> tuple[int, int]:
        return self._low, self._high

    def setValues(self, low: int, high: int):
        low = self._clamp(low)
        high = self._clamp(high)
        if high - low < self._minimum_span:
            high = self._clamp(low + self._minimum_span)
            low = self._clamp(high - self._minimum_span)
        self._commit(low, high)

    def minimumSpan(self) -> int:
        return self._minimum_span

    def setMinimumSpan(self, span: int):
        self._minimum_span = max(0, int(span))
        self.setValues(self._low, self._high)

    def setSingleStep(self, step: int):
        self._single_step = max(1, int(step))

    def setPageStep(self, step: int):
        self._page_step = max(1, int(step))

    def setTickInterval(self, interval: int):
        self._tick_interval = max(0, int(interval))
        self.updateGeometry()
        self.update()

    def _clamp(self, value) -> int:
        return max(self._minimum, min(int(round(value)), self._maximum))

    def _commit(self, low: int, high: int):
        if (low, high) == (self._low, self._high):
            return
        self._low, self._high = low, high
        self.update()
        self.valuesChanged.emit(low, high)

    def _move_low(self, value):
        low = min(self._clamp(value), self._high - self._minimum_span)
        self._commit(max(self._minimum, low), self._high)

    def _move_high(self, value):
        high = max(self._clamp(value), self._low + self._minimum_span)
        self._commit(self._low, min(self._maximum, high))

    def _move_band(self, value):
        width = self._grab_high - self._grab_low
        low = self._clamp(self._grab_low + (value - self._grab_value))
        low = min(low, self._maximum - width)
        self._commit(low, low + width)

    # --------------------------------------------------------------- geometry

    def _style_option(self, value: int) -> QtWidgets.QStyleOptionSlider:
        option = QtWidgets.QStyleOptionSlider()
        option.initFrom(self)
        option.orientation = QtCore.Qt.Orientation.Horizontal
        option.minimum = self._minimum
        option.maximum = self._maximum
        option.singleStep = self._single_step
        option.pageStep = self._page_step
        option.sliderPosition = value
        option.sliderValue = value
        option.upsideDown = False
        if self._tick_interval:
            option.tickPosition = QtWidgets.QSlider.TickPosition.TicksBelow
            option.tickInterval = self._tick_interval
        else:
            option.tickPosition = QtWidgets.QSlider.TickPosition.NoTicks
        return option

    def _sub_control_rect(
        self, sub_control: QtWidgets.QStyle.SubControl, value: int
    ) -> QtCore.QRect:
        return self.style().subControlRect(
            QtWidgets.QStyle.ComplexControl.CC_Slider,
            self._style_option(value),
            sub_control,
            self,
        )

    def _handle_rect(self, value: int) -> QtCore.QRect:
        return self._sub_control_rect(
            QtWidgets.QStyle.SubControl.SC_SliderHandle, value
        )

    def _value_at(self, x: int) -> int:
        """Translate a widget x coordinate into a slider value."""
        groove = self._sub_control_rect(
            QtWidgets.QStyle.SubControl.SC_SliderGroove, self._low
        )
        handle = self._handle_rect(self._low)
        span = groove.width() - handle.width()
        if span <= 0:
            return self._minimum
        position = x - groove.x() - handle.width() // 2
        return QtWidgets.QStyle.sliderValueFromPosition(
            self._minimum, self._maximum, position, span
        )

    def sizeHint(self) -> QtCore.QSize:
        option = self._style_option(self._low)
        thickness = self.style().pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_SliderThickness, option, self
        )
        if self._tick_interval:
            thickness += TICK_SPACE
        return self.style().sizeFromContents(
            QtWidgets.QStyle.ContentsType.CT_Slider,
            option,
            QtCore.QSize(SLIDER_LENGTH, thickness),
            self,
        )

    def minimumSizeHint(self) -> QtCore.QSize:
        hint = self.sizeHint()
        option = self._style_option(self._low)
        length = self.style().pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_SliderLength, option, self
        )
        return QtCore.QSize(length * 3, hint.height())

    # --------------------------------------------------------------- painting

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        style = self.style()

        # Draw the groove with the handle parked at the minimum: styles that
        # fill the groove up to the handle would otherwise shade everything
        # below our low handle, which is the part we are excluding.
        groove_option = self._style_option(self._minimum)
        groove_option.subControls = QtWidgets.QStyle.SubControl.SC_SliderGroove
        if self._tick_interval:
            groove_option.subControls |= (
                QtWidgets.QStyle.SubControl.SC_SliderTickmarks
            )
        style.drawComplexControl(
            QtWidgets.QStyle.ComplexControl.CC_Slider, groove_option, painter, self
        )

        low_rect = self._handle_rect(self._low)
        high_rect = self._handle_rect(self._high)
        groove_rect = self._sub_control_rect(
            QtWidgets.QStyle.SubControl.SC_SliderGroove, self._low
        )
        band = QtCore.QRect(
            low_rect.center().x(),
            groove_rect.center().y() - BAND_HEIGHT // 2,
            max(1, high_rect.center().x() - low_rect.center().x()),
            BAND_HEIGHT,
        )
        color = self.palette().highlight().color()
        if not self.isEnabled():
            color = self.palette().mid().color()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(band, BAND_HEIGHT / 2, BAND_HEIGHT / 2)

        for name, value in (("low", self._low), ("high", self._high)):
            option = self._style_option(value)
            option.subControls = QtWidgets.QStyle.SubControl.SC_SliderHandle
            if self._pressed in (name, "band"):
                option.state |= QtWidgets.QStyle.StateFlag.State_Sunken
                option.activeSubControls = (
                    QtWidgets.QStyle.SubControl.SC_SliderHandle
                )
            style.drawComplexControl(
                QtWidgets.QStyle.ComplexControl.CC_Slider, option, painter, self
            )

    # ----------------------------------------------------------------- input

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.MouseButton.LeftButton:
            event.ignore()
            return

        position = event.position().toPoint()
        value = self._value_at(position.x())
        low_rect = self._handle_rect(self._low)
        high_rect = self._handle_rect(self._high)

        if low_rect.contains(position) and high_rect.contains(position):
            # Handles touching: grab whichever one the drag can move.
            self._pressed = "low" if value < self._low else "high"
        elif low_rect.contains(position):
            self._pressed = "low"
        elif high_rect.contains(position):
            self._pressed = "high"
        elif self._low < value < self._high:
            self._pressed = "band"
            self._grab_value = value
            self._grab_low = self._low
            self._grab_high = self._high
        elif value <= self._low:
            self._pressed = "low"
            self._move_low(value)
        else:
            self._pressed = "high"
            self._move_high(value)

        if self._pressed != "band":
            self._active = self._pressed
        self.update()

    def mouseMoveEvent(self, event):
        if self._pressed is None:
            event.ignore()
            return
        value = self._value_at(event.position().toPoint().x())
        if self._pressed == "low":
            self._move_low(value)
        elif self._pressed == "high":
            self._move_high(value)
        else:
            self._move_band(value)

    def mouseReleaseEvent(self, event):
        if self._pressed is None:
            event.ignore()
            return
        self._pressed = None
        self.update()

    def keyPressEvent(self, event):
        steps = {
            QtCore.Qt.Key.Key_Left: -self._single_step,
            QtCore.Qt.Key.Key_Down: -self._single_step,
            QtCore.Qt.Key.Key_Right: self._single_step,
            QtCore.Qt.Key.Key_Up: self._single_step,
            QtCore.Qt.Key.Key_PageDown: -self._page_step,
            QtCore.Qt.Key.Key_PageUp: self._page_step,
        }
        key = event.key()
        if key == QtCore.Qt.Key.Key_Home:
            self._move_low(self._minimum)
            self._active = "low"
        elif key == QtCore.Qt.Key.Key_End:
            self._move_high(self._maximum)
            self._active = "high"
        elif key in steps:
            if self._active == "low":
                self._move_low(self._low + steps[key])
            else:
                self._move_high(self._high + steps[key])
        elif key == QtCore.Qt.Key.Key_Space:
            # No second focusable handle to Tab to, so Space swaps ends.
            self._active = "high" if self._active == "low" else "low"
        else:
            super().keyPressEvent(event)
            return
        event.accept()
