#!/usr/bin/python
import boto3 
import urllib2
import pymysql
import time
import json


with open('parameters.json') as json_data:
     params        = json.load(json_data).strip()
db_host            = params.get('database_host').strip()
db_port            = params.get('database_port').strip()
db_user            = params.get('database_user').strip()
db_pass            = params.get('database_pass').strip()
db_name            = params.get('database_name').strip()
aws_region         = params.get('aws_region_name').strip()
access_token       = params.get('access_token').strip()
secret_token       = params.get('secret_token').strip()
conn               = pymysql.connect(host=db_host, db=db_name, user=db_user, passwd=db_pass, autocommit=True)
curr               = conn.cursor()
ec2_client         = boto3.client('ec2',
                             aws_access_key_id=access_token,
                             aws_secret_access_key=secret_token,
                             region_name=aws_region,)
ec2_resource       = boto3.resource('ec2',
                             aws_access_key_id=access_token,
                             aws_secret_access_key=secret_token,
                             region_name=aws_region,)
route53            = boto3.client('route53',
                             aws_access_key_id=access_token,
                             aws_secret_access_key=secret_token,)
InstanceList       = []


def route53_api(public_ip, domain_name):
    changes           = []
    response          = route53.list_hosted_zones()
    hosted_zones      = []
    domain_name       = domain_name+'.'
    for data in response.get('HostedZones'):
        hosted_zones.append(data.get('Id'))
    
    
    for hosted_zone in hosted_zones:
        for resource_record_sets in route53.list_resource_record_sets(HostedZoneId=hosted_zone).get('ResourceRecordSets'):
            if resource_record_sets.get('Type') == 'A' and resource_record_sets.get('Name') == domain_name:
                 domain_name = domain_name.rstrip('.')
                 change = route53.change_resource_record_sets(
                          HostedZoneId=hosted_zone,
                          ChangeBatch={
                                       "Changes": [
                                                  {
                                                   "Action": "UPSERT",
                                                   "ResourceRecordSet": {
                                                          "Name": domain_name,
                                                          "Type": "A",
                                                          "TTL" : 1500,
                                                          "ResourceRecords": [
                                                           {
                                                              "Value": public_ip
                                                           },
                                                           ],
                                                   }
                                                   },
                                                   ]
                                      }
                          )
                 changes.append(change)
    return changes

def start_ec2():
    returndata        = {}

    curr.execute('select instance_id from instance_details where stopped_manually="N"')
    for instance in curr:
        InstanceList.append(instance[0])

    ec2_client.start_instances(InstanceIds=InstanceList, AdditionalInfo="Reserved")
    
    time.sleep(120)
    
    running_instances = ec2_resource.instances.filter(Filters=[{
                        'Name'  : 'instance-state-name',
                        'Values': ['running']}])

    for instance in running_instances:
        if instance.public_ip_address != "":
           returndata.update({instance.id:instance.public_ip_address})

    return returndata;

def update_db(data):
    dns              = []
    changes          = []
    data             = data.items()
    data.sort()
    for instance_id, public_ip in data:
        print "Currently updating the instance: %s with the latest ip address as %s" %(instance_id, public_ip)
        count        = curr.execute('select instance_id from instance_to_dns_map where instance_id="%s"' %instance_id)     

        if count > 0:
           curr.execute('update instance_to_dns_map set public_ip="%s" where instance_id="%s"' %(public_ip,instance_id))
           # Route 53 API call
           curr.execute('select domain_name from instance_to_dns_map where instance_id="%s"' %instance_id)
           for data in curr:
               dns.append(data[0].rstrip('.'))
           
           for domain in dns:
               changes.append(route53_api(public_ip, domain))

    return changes


if __name__ == "__main__" :
   instance_details = {}
   instance_details = start_ec2();
   changes          = update_db(instance_details);
   for change in changes:
       print change

   curr.close()

