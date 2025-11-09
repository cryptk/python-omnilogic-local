"""Utility functions for CLI operations.

This module provides helper functions for CLI commands, primarily for
accessing controller data within the Click context.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal, overload

import click

from pyomnilogic_local.api.api import OmniLogicAPI

if TYPE_CHECKING:
    from pyomnilogic_local.models.filter_diagnostics import FilterDiagnostics
    from pyomnilogic_local.models.mspconfig import MSPConfig
    from pyomnilogic_local.models.telemetry import Telemetry


async def get_omni(host: str) -> OmniLogicAPI:
    """Create an OmniLogicAPI instance for the specified controller.

    Args:
        host: Hostname or IP address of the OmniLogic controller

    Returns:
        Configured OmniLogicAPI instance ready for communication
    """
    return OmniLogicAPI(host, 10444, 5.0)


async def fetch_startup_data(omni: OmniLogicAPI) -> tuple[MSPConfig, Telemetry]:
    """Fetch MSPConfig and Telemetry from the controller.

    Args:
        omni: OmniLogicAPI instance for controller communication

    Returns:
        Tuple of (mspconfig, telemetry) data objects

    Raises:
        RuntimeError: If unable to fetch configuration or telemetry from controller
    """
    try:
        mspconfig = await omni.async_get_mspconfig()
        telemetry = await omni.async_get_telemetry()
    except Exception as exc:
        msg = f"[ERROR] Failed to fetch config or telemetry from controller: {exc}"
        raise RuntimeError(msg) from exc
    return mspconfig, telemetry


def ensure_connection(ctx: click.Context) -> None:
    """Ensure the controller connection is established and data is cached.

    This function should be called by subcommands that need to access the controller.
    It will only connect once, caching the connection and data in the context.

    Args:
        ctx: Click context object

    Raises:
        SystemExit: If connection to controller fails
    """
    # If already connected, return early
    if "OMNI" in ctx.obj:
        return

    # Get the host from context (stored by entrypoint)
    host = ctx.obj.get("HOST", "127.0.0.1")

    try:
        omni = asyncio.run(get_omni(host))
        mspconfig, telemetry = asyncio.run(fetch_startup_data(omni))
    except Exception as exc:
        click.secho(str(exc), fg="red", err=True)
        ctx.exit(1)

    ctx.obj["OMNI"] = omni
    ctx.obj["MSPCONFIG"] = mspconfig
    ctx.obj["TELEMETRY"] = telemetry


@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[True]) -> str: ...


@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[False]) -> FilterDiagnostics: ...


async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: bool) -> FilterDiagnostics | str:
    """Retrieve filter diagnostics from the controller.

    Args:
        omni: OmniLogicAPI instance for controller communication
        pool_id: System ID of the Body Of Water
        filter_id: System ID of the filter/pump
        raw: If True, return raw XML string; if False, return parsed FilterDiagnostics object

    Returns:
        FilterDiagnostics object or raw XML string depending on raw parameter
    """
    return await omni.async_get_filter_diagnostics(pool_id, filter_id, raw=raw)
