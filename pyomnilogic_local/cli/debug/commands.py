# Need to figure out how to resolve the 'Untyped decorator makes function "..." untyped' errors in mypy when using click decorators
# mypy: disable-error-code="misc"
import asyncio
from typing import Literal, overload

import click

from pyomnilogic_local.api import OmniLogicAPI
from pyomnilogic_local.cli.utils import async_get_mspconfig, async_get_telemetry
from pyomnilogic_local.models.filter_diagnostics import FilterDiagnostics


@click.group()
@click.option("--raw/--no-raw", default=False, help="Output the raw XML from the OmniLogic, do not parse the response")
@click.pass_context
def debug(ctx: click.Context, raw: bool) -> None:
    # Container for all get commands

    ctx.ensure_object(dict)
    ctx.obj["RAW"] = raw


@debug.command()
@click.pass_context
def get_mspconfig(ctx: click.Context) -> None:
    mspconfig = asyncio.run(async_get_mspconfig(ctx.obj["OMNI"], ctx.obj["RAW"]))
    click.echo(mspconfig)


@debug.command()
@click.pass_context
def get_telemetry(ctx: click.Context) -> None:
    telemetry = asyncio.run(async_get_telemetry(ctx.obj["OMNI"], ctx.obj["RAW"]))
    click.echo(telemetry)


@debug.command()
@click.pass_context
def get_alarm_list(ctx: click.Context) -> None:
    alarm_list = asyncio.run(async_get_alarm_list(ctx.obj["OMNI"]))
    click.echo(alarm_list)


async def async_get_alarm_list(omni: OmniLogicAPI) -> str:
    alarm_list = await omni.async_get_alarm_list()
    return alarm_list


@debug.command()
@click.option("--pool-id", help="System ID of the Body Of Water the filter is associated with")
@click.option("--filter-id", help="System ID of the filter to request diagnostics for")
@click.pass_context
def get_filter_diagnostics(ctx: click.Context, pool_id: int, filter_id: int) -> None:
    filter_diags = asyncio.run(async_get_filter_diagnostics(ctx.obj["OMNI"], pool_id, filter_id, ctx.obj["RAW"]))
    if ctx.obj["RAW"]:
        click.echo(filter_diags)
    else:
        drv1 = chr(filter_diags.get_param_by_name("DriveFWRevisionB1"))
        drv2 = chr(filter_diags.get_param_by_name("DriveFWRevisionB2"))
        drv3 = chr(filter_diags.get_param_by_name("DriveFWRevisionB3"))
        drv4 = chr(filter_diags.get_param_by_name("DriveFWRevisionB4"))
        dfw1 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB1"))
        dfw2 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB2"))
        dfw3 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB3"))
        dfw4 = chr(filter_diags.get_param_by_name("DisplayFWRevisionB4"))
        pow1 = filter_diags.get_param_by_name("PowerMSB")
        pow2 = filter_diags.get_param_by_name("PowerLSB")
        errs = filter_diags.get_param_by_name("ErrorStatus")
        click.echo(
            f"DRIVE FW REV: {drv1}{drv2}.{drv3}{drv4}\n"
            f"DISPLAY FW REV: {dfw1}{dfw2}.{dfw3}.{dfw4}\n"
            f"POWER: {pow1:x}{pow2:x}W\n"
            f"ERROR STATUS: {errs}"
        )


@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[True]) -> str: ...
@overload
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: Literal[False]) -> FilterDiagnostics: ...
async def async_get_filter_diagnostics(omni: OmniLogicAPI, pool_id: int, filter_id: int, raw: bool) -> FilterDiagnostics | str:
    filter_diags = await omni.async_get_filter_diagnostics(pool_id, filter_id, raw=raw)
    return filter_diags


@debug.command()
@click.pass_context
def get_log_config(ctx: click.Context) -> None:
    log_config = asyncio.run(async_get_log_config(ctx.obj["OMNI"]))
    click.echo(log_config)


async def async_get_log_config(omni: OmniLogicAPI) -> str:
    log_config = await omni.async_get_log_config()
    return log_config
