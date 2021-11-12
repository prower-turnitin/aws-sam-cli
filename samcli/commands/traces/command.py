"""
CLI command for "traces" command
"""
import logging

import click

from samcli.cli.cli_config_file import configuration_option, TomlProvider
from samcli.cli.main import pass_context, common_options as cli_framework_options, aws_creds_options, print_cmdline_args
from samcli.commands._utils.options import common_observability_options
from samcli.lib.telemetry.metric import track_command
from samcli.lib.utils.version_checker import check_newer_version
from samcli.commands._utils.experimental import ExperimentalFlag, force_experimental

LOG = logging.getLogger(__name__)

HELP_TEXT = """
[Beta Feature] Use this command to fetch AWS X-Ray traces generated by your stack.\n
"""


@click.command("traces", help=HELP_TEXT, short_help="[Beta Feature] Fetch AWS X-Ray traces")
@configuration_option(provider=TomlProvider(section="parameters"))
@click.option(
    "--trace-id",
    "-ti",
    multiple=True,
    help="Fetch specific trace by providing its id",
)
@common_observability_options
@cli_framework_options
@force_experimental(config_entry=ExperimentalFlag.Accelerate)  # pylint: disable=E1120
@aws_creds_options
@pass_context
@track_command
@check_newer_version
@print_cmdline_args
def cli(
    ctx,
    trace_id,
    start_time,
    end_time,
    tail,
    unformatted,
    config_file,
    config_env,
):
    """
    `sam traces` command entry point
    """
    do_cli(trace_id, start_time, end_time, tail, unformatted, ctx.region)


def do_cli(trace_ids, start_time, end_time, tailing, unformatted, region):
    """
    Implementation of the ``cli`` method
    """
    from datetime import datetime
    import boto3
    from samcli.commands.logs.logs_context import parse_time
    from samcli.commands.traces.traces_puller_factory import generate_trace_puller
    from samcli.lib.utils.boto_utils import get_boto_config_with_user_agent

    sanitized_start_time = parse_time(start_time, "start-time")
    sanitized_end_time = parse_time(end_time, "end-time") or datetime.utcnow()

    boto_config = get_boto_config_with_user_agent(region_name=region)
    xray_client = boto3.client("xray", config=boto_config)

    # generate puller depending on the parameters
    puller = generate_trace_puller(xray_client, unformatted)

    if trace_ids:
        puller.load_events(trace_ids)
    elif tailing:
        puller.tail(sanitized_start_time)
    else:
        puller.load_time_period(sanitized_start_time, sanitized_end_time)
