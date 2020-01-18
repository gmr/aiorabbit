Supported AMQ Methods
=====================

| AMQ Method                     | Completed |
|--------------------------------|:---------:|
| Basic.Ack                      |           |
| Basic.Cancel                   |           |
| Basic.Consume                  |           |
| Basic.Deliver                  |           |
| Basic.Get                      |           |
| Basic.Nack                     |           |
| Basic.Publish                  |     ✔     |
| Basic.Qos                      |           |
| Basic.Recover                  |           |
| Basic.RecoverAsync             |     ✗     |
| Basic.Reject                   |           |
| Basic.Return                   |           |
| Channel.Close                  |           |
| Channel.Flow                   |           |
| Channel.Open                   |           |
| Confirm.Select                 |     ✔     |
| Connection.Blocked             |     ✔     |
| Connection.Close               |     ✔     |
| Connection.Open                |     ✔     |
| Connection.Secure              |     ?     |
| Connection.Start               |     ✔     |
| Connection.Tune                |     ✔     |
| Connection.Unblocked           |     ✔     |
| Connection.UpdateSecret        |           |
| Exchange.Bind                  |           |
| Exchange.Declare               |           |
| Exchange.Delete                |           |
| Exchange.Unbind                |           |
| Queue.Bind                     |           |
| Queue.Declare                  |           |
| Queue.Delete                   |           |
| Queue.Purge                    |           |
| Queue.Unbind                   |           |
| Tx.Commit                      |           |
| Tx.Rollback                    |           |
| Tx.Select                      |           |
  
  ✗ - Not supported or deprecated in RabbitMQ
  ? - Connection.Secure can be used with a plugin, need use case for implementation.
