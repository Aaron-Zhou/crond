Crond for OpenShift
===================

This repo contains Dockerfile and [OpenShift](https://github.com/openshift/origin/) templates to run Crond.

Jobs may be configured to run as [Kubernetes Jobs](http://kubernetes.io/docs/user-guide/jobs/), from within a user defined docker images.

It uses [ConfigMaps](http://kubernetes.io/docs/user-guide/configmap/) for jobs configuration and definition.

_This is a temporary solution until [CronJobs](http://kubernetes.io/docs/user-guide/cron-jobs/) hit production_

Usage
-----

Create the ImageStream in your project and import it:

    $ oc create -f imagestream.yaml
    $ oc import-image crond

Now, let's create a cron application named `cron`:

    $ oc process -f template.yaml -v NAME=cron,JOB_IMAGE_NAMESPACE=myproj,JOB_IMAGE_NAME=app | oc create -f -

Valid parameters are:

- `NAME`: the name of the app
- `CRON_SCHEDULE`: Cron schedule to excute the job
- `COMMAND`: Command to execute
- `DOCKER_REGISTRY`, `JOB_IMAGE_NAMESPACE`, `JOB_IMAGE_NAME` and `JOB_IMAGE_TAG`: Define image to use to run the job
- `JOBS_DIR`: Where to mount job's ConfigMap files

It will create the following objects:

- DeploymentConfig/cron: the crond itself, plus job management scritps from dir `root/`
- ConfigMap/cron-config: crond configuration
- ConfigMas/cron-jobs: list of Job objects to execute


Configure
---------

Configs for both crond and Jobs are stored in ConfigMaps

    $ oc edit configmaps/cron-config
    $ oc edit configmaps/cron-jobs

In order to create new jobs simply add entries to `ConfigMap/cron-jobs` under key `data`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ${NAME}-jobs
data:
  myjob: |-
    # Here goes a Pod template
```

Then add an entry to execute your job `myjob` in `ConfigMaps/cron-config`:

    # runs job `myjob` everydat at 3:05AM
    5 3 * * * cron run-job myjob

After editing ConfigMaps you must re-deploy the application:

    $ oc deploy cron --latest

Job cleanup
-----------

The docker image ships with `clean-jobs` script to delete old Job objects and it's Pods.
It's highly recomended to run it periodically:

    */5  *  *  *  * cron clean-jobs

