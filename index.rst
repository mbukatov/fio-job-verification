==================================================
 Data verification of previously written fio data
==================================================

:author: Martin Bukatovič
:date: 2020-04-15

Flexible I/O Tester
===================

`Fio tool`_ performs a IO workload based on a description from a command line
or a `fio job file`_ (there can be multiple workloads described in a single job
file).

.. nextslide::

Example of a simple workload which consumes all available space on a given
filesystem.

Job file ``workload.fio``:

.. code:: ini

    [simple-write]
    readwrite=write
    buffered=1
    blocksize=4k
    ioengine=libaio
    directory=/mnt/target
    fill_fs=1

Execution of the workload:

.. code:: shell

    $ fio --output-format=json workload.fio

Kubernetes Jobs
===============

`Job`_ creates one (or more) Pods and makes sure that it (or any number as
specified) completes with success.

See ``controllers/job.yaml`` example:

.. code:: yaml

    apiVersion: batch/v1
    kind: Job
    metadata:
      name: pi
    spec:
      template:
        spec:
          containers:
          - name: pi
            image: perl
            command: ["perl",  "-Mbignum=bpi", "-wle", "print bpi(2000)"]
          restartPolicy: Never
      backoffLimit: 4

.. note::

    A time for demo on OCP cluster, if suitable.

Running fio as k8s Job
======================

Job is a good k8s abstraction for fio workload executions.
Let's see a simple example how this would look like.

PersistentVolumeClaim to provision storage:

.. code:: yaml

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: fio-target
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 10Gi
      storageClassName: ocs-storagecluster-ceph-rbd

.. nextslide::

`ConfigMap`_ to specify a workload via `fio job file`_:

.. code:: yaml

    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: fio-config
    data:
      workload.fio: |
        [simple-write]
        readwrite=write
        buffered=1
        blocksize=4k
        ioengine=libaio
        directory=/mnt/target
        fill_fs=1

.. nextslide::

And finally the `Job`_ itself:

.. code:: yaml

    apiVersion: batch/v1
    kind: Job
    metadata:
      name: fio
    spec:
      backoffLimit: 1
      template:
        metadata:
          name: fio
        spec:
          containers:
            SEE-NEXT-SLIDE
          restartPolicy: Never
          volumes:
            SEE-NEXT-SLIDE

.. nextslide::

``spec.template.spec.volumes``:

.. code:: yaml

          - name: fio-target
            persistentVolumeClaim:
              claimName: fio-target
          - name: fio-config-volume
            configMap:
              name: fio-config

.. nextslide::

``spec.template.spec.containers``:

.. code:: yaml

          - name: fio
            image: quay.io/mbukatov/mbukatov-fedora-fio:latest
            command:
            - /usr/bin/fio
            - --output-format=json
            - /etc/fio/workload.fio
            volumeMounts:
            - mountPath: /mnt/target
              name: fio-target
            - mountPath: /etc/fio
              name: fio-config-volume

.. note::

    A time for demo on OCS cluster, showing similar finished Job in
    OCP Console.

Usage of fio Jobs in ocs-ci
===========================

Right now, we use fio Jobs for:

- `storage utilization`_ `workload fixtures`_ (focused on metrics and alerting
  use cases)
- `data verification tests`_ after cluster disruption (temporary shutdown,
  reboot or upgrade)
- `running workload during upgrade`_

Data verification tests
=======================

#. Test case writes data with a checksum to a persistent volume, and makes sure
   the volume is not deleted when a test namespace is removed during test
   teardown (eg. `test_workload_with_checksum`_).

#. A disruptive operation affecting whole or most of the cluster nodes is
   performed, such as temporary shutdown, reboot or upgrade.

#. Another test case looks for the volume created by the first test (via
   label), and runs a data verification job (eg.
   `test_workload_with_checksum_verify`_).

#. If necessary, the data verification test case can be executed again
   to make sure the data are still there (to make this possible, the PV is not
   explicitly removed).

Reusing already existing PV
===========================

`Kubernetes Dynamic provisioning`_:
    When none of the static PVs the administrator created match a user’s
    PersistentVolumeClaim, the cluster may try to dynamically provision a volume
    specially for the PVC. This provisioning is based on StorageClasses ...

This means that OCS could bind existing released PV to new PVC request,
assuming that the volume no longer contains a ``claimRef`` referencing the
original PVC, as explained in `How to manually reclaim and reuse OpenShift
Persistent volumes that are "Released"`_.

.. nextslide::

Test case which writes data with checksum will also:

- `change Reclaim Policy of a PersistentVolume of the PV`_ to ``Retain``
- label the PV so that it can be identified later

So that when the test case namespace is removed during teardown and we look
for the volume via the label:

.. code:: shell

    $ oc get pv -l "fixture" -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.persistentVolumeReclaimPolicy}{" "}{.status.phase}{"\n"}{end}'
    pvc-28f68a39-6df7-11ea-adc9-005056bee634 Retain Released

We see that the PV is still around, with ``Retain`` reclaim policy and in
``Released`` state.

.. nextslide::

Test case which reads and validates data on the persistent volume then needs
to:

- locale the PV using label
- remove ``ClaimRef`` from the volume, for the PV to move into ``Available``
  state (in which it could be bound to matching PVC again)
- use the same PVC as did the data writing job

So that the verification job is provisioned and it's PVC is bound to the
persistent volume created during the first data writing test.

Validation of data created by fio
=================================

Original idea was to add ``verify=crc32c`` in the `fio job file`_ which writes
data on the volume.

And then later when verification of the data is needed, run the same job again,
but this time:

- reuse the persistent volume instead of provisioning new one
- adding ``verify_only`` option in the `fio job file`_

But this showed problematic from debugging perspective (dealing with
*misconfigured vmware lab*, fio bugs like `fio #732`_ and issues I created on
purpose).

.. nextslide::

So instead of buildin fio data verification feature, I'm using plain
``sha1sum`` tool:

- when fio finishes writing, ``sha1sum`` computes checksum of a file just
  created by fio and store resulting ``fio.sha1sum`` file on the volume next
  the the data file

- during data verification run, ``sha1sum -c fio.sha1sum`` command
  is executed

.. _`Fio tool`: https://fio.readthedocs.io/en/latest
.. _`fio job file`: https://fio.readthedocs.io/en/latest/fio_doc.html#job-file-format
.. _`Job`: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/
.. _`ConfigMap`: https://kubernetes.io/docs/concepts/workloads/controllers/jobs-run-to-completion/
.. _`fio #732`: https://github.com/axboe/fio/issues/732
.. _`workload fixtures`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/ocs_ci/utility/workloadfixture.py
.. _`storage utilization`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/tests/manage/monitoring/conftest.py#L322
.. _`data verification tests`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/tests/manage/monitoring/test_workload_with_distruptions.py
.. _`running workload during upgrade`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/tests/ecosystem/upgrade/conftest.py
.. _`test_workload_with_checksum`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/tests/manage/monitoring/test_workload_with_distruptions.py#L50
.. _`test_workload_with_checksum_verify`: https://github.com/red-hat-storage/ocs-ci/blob/de5d0abb024121dc82c28be26ce741ba94fb2f2b/tests/manage/monitoring/test_workload_with_distruptions.py#L64
.. _`change Reclaim Policy of a PersistentVolume of the PV`: https://kubernetes.io/docs/tasks/administer-cluster/change-pv-reclaim-policy/
.. _`Kubernetes Dynamic provisioning`: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#dynamic
.. _`How to manually reclaim and reuse OpenShift Persistent volumes that are "Released"`: https://access.redhat.com/solutions/4651451
