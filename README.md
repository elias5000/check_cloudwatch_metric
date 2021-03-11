# check_cloudwatch_metric

Icinga/Nagios check to test an AWS CloudFormation metric against thresholds.

## Required Modules
* boto3

## Usage
    usage: check_cloudwatch_metric.py [-h] --name NAME --namespace NAMESPACE
                                      --warning WARNING --critical CRITICAL
                                      [--dimensions DIMENSIONS] [--last_state]
                                      [--minutes MINUTES] [--prefix PREFIX]
                                      [--region REGION] [--statistics STATISTICS]

    optional arguments:
      -h, --help            show this help message and exit
      --dimensions DIMENSIONS
                            metric dimensions in form "Name1:Value1,Name2:Value2"
      --last_state          use last known value
      --minutes MINUTES     time window to aggregate for statistic
      --prefix PREFIX       metric namespace prefix (default: AWS)
      --region REGION       AWS region name
      --statistics STATISTICS
                            statistics to compare (default: Average)

    required arguments:
      --name NAME           metric name (e.g. CPUUtilization)
      --namespace NAMESPACE
                            metric namespace (e.g. EC2)
      --warning WARNING     warning threshold
      --critical CRITICAL   critical threshold

    thresholds and ranges:
      Threshold ranges are in Nagios format:
      https://nagios-plugins.org/doc/guidelines.html#THRESHOLDFORMAT