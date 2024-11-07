from datetime import timedelta
import logging
from typing import Callable

from homeassistant.core import HomeAssistant

from custom_components.dual_smart_thermostat.hvac_action_reason.hvac_action_reason import (
    HVACActionReason,
)
from custom_components.dual_smart_thermostat.hvac_controller.generic_controller import (
    GenericHvacController,
)
from custom_components.dual_smart_thermostat.hvac_controller.hvac_controller import (
    HvacEnvStrategy,
)
from custom_components.dual_smart_thermostat.managers.environment_manager import (
    EnvironmentManager,
)
from custom_components.dual_smart_thermostat.managers.opening_manager import (
    OpeningManager,
)

_LOGGER = logging.getLogger(__name__)


class CoolerHvacController(GenericHvacController):

    def __init__(
        self,
        hass: HomeAssistant,
        entity_id,
        min_cycle_duration: timedelta,
        environment: EnvironmentManager,
        openings: OpeningManager,
        turn_on_callback: Callable,
        turn_off_callback: Callable,
        always_on: bool=False
    ) -> None:
        self._controller_type = self.__class__.__name__
        self._always_on = always_on

        super().__init__(
            hass,
            entity_id,
            min_cycle_duration,
            environment,
            openings,
            turn_on_callback,
            turn_off_callback,
        )
        
    # override
    async def async_control_device_when_on(
        self,
        strategy: HvacEnvStrategy,
        any_opening_open: bool,
        time=None,
    ) -> None:
        
        if (not self._always_on and strategy.hvac_goal_reached) or any_opening_open:
            _LOGGER.info(
                "Turning off entity due to hvac goal reached or opening is open %s",
                self.entity_id,
            )

            await self.async_turn_off_callback()

            if strategy.hvac_goal_reached:
                _LOGGER.debug("setting hvac_action_reason goal reached")
                self._hvac_action_reason = strategy.goal_reached_reason()
            if any_opening_open:
                _LOGGER.debug("setting hvac_action_reason opening")
                self._hvac_action_reason = HVACActionReason.OPENING
        elif time is not None and not any_opening_open:
            # The time argument is passed only in keep-alive case
            _LOGGER.info(
                "Keep-alive - Turning on entity (from active) %s",
                self.entity_id,
            )
            await self.async_turn_on_callback()
            self._hvac_action_reason = strategy.goal_not_reached_reason()
        else:
            _LOGGER.debug("No case matched when - keep device on")
