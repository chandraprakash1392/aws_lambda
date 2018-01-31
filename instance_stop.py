#!/usr/bin/python

import boto3
import pymysql
import urllib2
import json

def route53_api(public_ip):
    hosted_zones     = []
    domain_names     = []

    for data in route53.list_hosted_zones().get('HostedZones'):
        hosted_zones.append(data.get('Id').split('/')[2]) 
    
    for hosted_zone in hosted_zones:
        for recordsets in route53.list_resource_record_sets(HostedZoneId=hosted_zone).get('ResourceRecordSets'):
            if public_ip == recordsets.get('ResourceRecords')[0].get('Value'):
               domain_names.append(recordsets.get('Name'))

    return domain_names

if __name__ == "__main__":
# Fetching the creds from parameters.json file
  with open('parameters.json') as json_data:
       params        = json.load(json_data)

  db_host            = params.get('database_host')
  db_port            = params.get('database_port')
  db_user            = params.get('database_user')
  db_pass            = params.get('database_pass')
  db_name            = params.get('database_name')
  aws_region         = params.get('aws_region_name')
  access_token       = params.get('access_token')
  secret_token       = params.get('secret_token')
 
# Check for all the instances present in the databases or not
  my_instance_id     = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id/').read()
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
  instances          = []
    
  running_instances  = ec2_resource.instances.filter(Filters = [{
                      'Name'  : 'instance-state-name',
                      'Values': ['running']}])

  stopped_instance   = ec2_resource.instances.filter(Filters = [{
                      'Name'  : 'instance-state-name',
                      'Values': ['stopped']}])

  for instance in running_instances:
    if instance.public_ip_address != "" and str(instance.id) != str(my_instance_id):
      public_ip      = instance.public_ip_address
      instance_id    = instance.id
      instance_name  = instance.tags[0].get("Value")
      print "Currently performing on instance: %s, public_ip: %s" %(instance_id, public_ip)

      # Checking for entry in the instance_details database. If not present, it will insert, else update #
      count          = curr.execute('select * from instance_details where instance_id="%s"' %instance_id)
      if count == 0:
         curr.execute('insert into instance_details (instance_id, instance_state, stopped_manually) values("%s", "running", "N")' %instance_id)
      else:
         curr.execute('update instance_details set stopped_manually="N" where instance_id="%s"' %instance_id)

      # Checking for entry in instance_to_dns_map database. If any new entry present, insert it #
      count          = curr.execute('select * from instance_to_dns_map where public_ip="%s"' %public_ip)
      if count == 0:
         domains_active = route53_api(public_ip) 
         for domain in domains_active:
             curr.execute('insert into instance_to_dns_map (instance_id, domain_name, public_ip, instance_name) values("%s", "%s", "%s", "%s")' %(instance_id, domain, public_ip, instance_name))
      else:
         domains_active = route53_api(public_ip)
         for domain in domains_active:
             count = curr.execute('select * from instance_to_dns_map where instance_id="%s" and domain_name="%s"' %(instance_id, domain))
         if count == 0:
            curr.execute('insert into instance_to_dns_map (instance_id, domain_name, public_ip, instance_name) values("%s", "%s", "%s", "%s")' %(instance_id, domain, public_ip, instance_name))
   
  for instance in stopped_instance:
      instance_id    = instance.id
      count          = curr.execute('select * from instance_details where instance_id="%s"' %instance_id)
      if count == 0:
         curr.execute('insert into instance_details (instance_id, instance_state, stopped_manually) values("%s", "stopped", "Y")' %instance_id)
      else:
         curr.execute('udpate instance_details set stopped_manually="N" where instance_id="%s"' %instance_id)


# Stopping the instances by reading instance_details DB
  curr.execute('select instance_id from instance_details')
  for instance in curr:
      if str(instance[0]) != str(my_instance_id):
         instances.append(instance[0])
  ec2_client.stop_instances(InstanceIds=instances) 


  curr.close()
