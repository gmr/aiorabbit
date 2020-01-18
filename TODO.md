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
| Basic.Publish                  |   :+1:    |
| Basic.Qos                      |           |
| Basic.Recover                  |           |
| Basic.RecoverAsync             |   :-1:    |
| Basic.Reject                   |           |
| Basic.Return                   |           |
| Channel.Close                  |           |
| Channel.Flow                   |           |
| Channel.Open                   |           |
| Confirm.Select                 |   :+1:    |
| Connection.Blocked             |   :+1:    |
| Connection.Close               |   :+1:    |
| Connection.Open                |   :+1:    |
| Connection.Secure              |  :mag:    |
| Connection.Start               |   :+1:    |
| Connection.Tune                |   :+1:    |
| Connection.Unblocked           |   :+1:    |
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
  
:-1: - Not supported or deprecated in RabbitMQ

:mag: - Connection.Secure can be used with a plugin, need use case for implementation.
