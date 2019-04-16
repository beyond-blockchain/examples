Tickets
==========
This app allows a user to do the following:
* define and switch among users
* define and switch among ticket services
* issue tickets for a user
* redeem tickets
* transfer tickets from a user to another user
* show status (holders, etc.) of tickets

# How to use
1. Start bbc_core.py
  * See [tutorials](https://github.com/beyond-blockchain/bbc1/tree/develop/docs)
  * Those tutorials are in Japanese for the time being.
2. Create a domain.
    ```
    python tickets.py setup
    ```
3. User commands
    * Define a user
        ```
        python tickets.py def-user [username]
        ```
    * Show users
        ```
        python tickets.py user
        ```
    * Switch to a user
        ```
        python tickets.py user [username]
        ```
    * Replace the key-pair for a user
        ```
        python tickets.py new-keypair [username]
        ```
4. Service commands
    * Define a service
        ```
        python tickets.py def-service [name]
        ```
    * Show services
        ```
        python tickets.py service
        ```
    * Switch to a currency
        ```
        python tickets.py service [name]
        ```
    * Issue a ticket for a user
        ```
        python tickets.py issue [description] [username]
        ```
    * Transfer the ticket to a user
        ```
        python tickets.py transfer [ticket_id] [username]
        ```
    * Rdeem the ticket from a user
        ```
        python tickets.py redeem [ticket_id]
        ```
      
5. Status commands
    * Show the currency status (not implemented yet)
        ```
        python tickets.py status
        ```
    * Show the service status for a user
        ```
        python tickets.py status [username]
        ```
