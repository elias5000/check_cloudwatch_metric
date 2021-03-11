#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta

import boto3

STATE_OK = 0
STATE_WARN = 1
STATE_CRIT = 2
STATE_UNKNOWN = 3


class Metric:
    def __init__(self, **kwargs):
        self.dimensions = kwargs.get('dimensions')
        self.last_state = kwargs.get('last_state')
        self.minutes = int(kwargs.get('minutes'))
        self.name = kwargs.get('name')
        self.namespace = kwargs.get('namespace')
        self.prefix = kwargs.get('prefix', 'AWS')
        self.region = kwargs.get('region', 'eu-central-1')
        self.statistics = kwargs.get('statistics')

    def get_client(self):
        """
        Return cloudwatch client for region
        :return:
        """
        return boto3.session.Session(region_name=self.region).resource('cloudwatch')

    def get_metric(self):
        """
        Return metric resource by name
        :return:
        """
        return self.get_client().Metric("{}/{}".format(self.prefix, self.namespace), self.name)

    def get_dimensions(self):
        """
        Return dimensions for request
        :return:
        """
        if not self.dimensions:
            return []

        dimensions = []
        for pair in self.dimensions.split(','):
            bits = pair.split(':')
            dimensions.append({
                'Name': bits[0],
                'Value': bits[1]
            })
        return dimensions

    def get_statistics(self, metric=None, offset=0):
        """
        Return statistics for resource
        :param metric:
        :param offset:
        :return:
        """
        if offset > 20:
            return None

        if metric is None:
            metric = self.get_metric()

        statistics = metric.get_statistics(
            Dimensions=self.get_dimensions(),
            StartTime=self.start_time(offset),
            EndTime=self.end_time(offset),
            Period=300,
            Statistics=[self.statistics]
        )
        if not statistics['Datapoints'] and self.last_state:
            statistics = self.get_statistics(metric, offset + 1)

        return statistics

    def get_current_value(self):
        """
        Return latest value from statistics
        :return:
        """
        statistics = self.get_statistics()
        if not statistics['Datapoints']:
            return None

        return statistics['Datapoints'][-1][self.statistics]

    def start_time(self, offset=0):
        """
        Return start time
        :param offset:
        :return:
        """
        return datetime.utcnow() - timedelta(minutes=(self.minutes + offset))

    @staticmethod
    def end_time(offset=0):
        """
        Return end time
        :param offset:
        :return:
        """
        return datetime.utcnow() - timedelta(minutes=offset)


def compare_range(value, window):
    """
    Compare value with nagios range and return True if value is within boundaries
    :param value:
    :param window:
    :return:
    """
    incl = False
    if window[0] == '@':
        incl = True
        window = window[1:]

    if ":" not in window:
        start = 0
        stop = window
    else:
        bits = window.split(':')
        start = bits[0]
        stop = bits[1] if bits[1] else '~'

    start = None if start == '~' else float(start)
    stop = None if stop == '~' else float(stop)
    if start and ((incl and value <= start) or (not incl and value < start)):
        return False
    if stop and ((incl and value >= stop) or (not incl and value > stop)):
        return False

    return True


def compare(value, warn, crit):
    """
    Compare value with thresholds and return status
    :param value:
    :param warn:
    :param crit:
    :return:
    """
    if not compare_range(value, crit):
        return STATE_CRIT
    if not compare_range(value, warn):
        return STATE_WARN
    return STATE_OK


def main():
    parser = ArgumentParser()
    required = parser.add_argument_group('required arguments')
    required.add_argument('--name', help='Metric name (e.g. CPUUtilization)', required=True)
    required.add_argument('--namespace', help='Metric namespace (e.g. EC2)', required=True)
    required.add_argument('--warning', help='Warning threshold', required=True)
    required.add_argument('--critical', help='Critical threshold', required=True)

    parser.add_argument('--dimensions',
                        help='Metric dimensions in form "Name1:Value1,Name2:Value2"')
    parser.add_argument('--last_state', help='Use last known value', action='store_true')
    parser.add_argument('--minutes', help='Time window to aggregate for statistic', default='5')
    parser.add_argument('--prefix', help='Metric namespace prefix (default: AWS)', default='AWS')
    parser.add_argument('--region', help='AWS region name', default='eu-central-1')
    parser.add_argument('--statistics',
                        help='Statistics to compare (Default: Average)', default='Average')

    args = parser.parse_args()

    metric = Metric(
        dimensions=args.dimensions,
        last_state=args.last_state,
        minutes=args.minutes,
        name=args.name,
        namespace=args.namespace,
        prefix=args.prefix,
        region=args.region,
        statistics=args.statistics
    )
    value = metric.get_current_value()
    if not value:
        print("UNKNOWN - No value returned from AWS")
        sys.exit(STATE_UNKNOWN)

    status = compare(value, args.warning, args.critical)
    if status == STATE_OK:
        print("OK - Value of {} is within boundaries".format(value))
    elif status == STATE_WARN:
        print("WARNING - Value of {} triggers warning threshold".format(value))
    else:
        print("CRITICAL - Value of {} triggers alarm threshold".format(value))

    sys.exit(status)


if __name__ == "__main__":
    main()
