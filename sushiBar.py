import redis

#connect to redis
client = redis.Redis(host="localhost", port="6379", db=0, charset="utf-8", decode_responses=True)
print("Connection status:", client.ping())

#print list of sushi
def printSushiSet():
    print("---Sushi list---:") 
    print(client.smembers('sushi'))
    print("------------------")

# add new sushi
def newSushiInput(name, count):
    client.sadd( 'sushi', name)
    client.set(name, count)  

# function that checks if the given key exists
def check(name):
    return client.exists(name) 

# additional list of usernames and userIDs
def registerUsers(userID, username):
    client.lpush("users", username)
    client.set(username, userID)

def payment(username, orderID):
    print("THE START OF THE TRANSACTION\n")
    userID = client.get(username)
    print(userID)
    while True:
        try:
            p = client.pipeline()
            keys = client.hgetall(username + orderID)
            p.watch(userID)
            print("watching")
            for key in keys:
                p.watch(key)
            p.multi()
            p.hincrby(userID, 'ricepoints', -int(client.hget(orderID, "price")))
            for key in keys: 
                p.incrby(key, -int(client.hget(username + orderID, key)))
            p.execute()
            break
        except redis.WatchError:
            continue
        finally:
            p.reset()
    print("THE END OF THE TRANSACTION\n")


# additional list of cartID and usernames
def shoppingCarts(cartID, username):
    #p = client.pipeline()
    client.lpush("carts", username)
    client.set(username, cartID)

# create new order
def createOrder(username):
    client.incr('orderNum')
    orderID = "order" + str(client.get('orderNum')) 
    print(orderID)
    client.hset(orderID, 'username', username)
    client.hset(orderID, 'shoppingCartID', username + orderID)
    client.hset(orderID, 'price', 0)    
    return orderID

# add sushi to the shopping cart
def addSushiToTheShoppingCart(username, wantedSushi, howMany, orderID): 
    #p = client.pipeline()
    #p.watch(wantedSushi)
    client.hset(username + orderID, wantedSushi, howMany)
    client.hincrby(orderID, 'price', howMany) # increase total price of order

# delete order
def deleteOrder(orderID, username):
    print("Your order will be deleted soon")
    client.hdel(orderID)
    client.hdel(username + orderID)
    print("Order deleted succesfully")

def selectSushi(username, orderID):
    wantedSushi = input("Type the name of sushi you want to order\n")

    #check if sushi exists
    if check(wantedSushi) == 0:
        print("Wrong sushi, start ordering again")
        selectSushi(username, orderID)
    
    #selecting sushi
    elif check(wantedSushi) == 1:
        print("How many of ", wantedSushi, " sushi you want to order? (in stock: ", client.get(wantedSushi), " )")
        howMany = input()
        #check if sushi is in stock and start adding (not updating)
        if howMany <= client.get(wantedSushi):
            addSushiToTheShoppingCart(username, wantedSushi, howMany, orderID)   
            ans = input("Want to add more sushis? 1 - YES, 0 - NO") 
            if ans.isdigit() and int(ans) == 1:
                selectSushi(username, orderID)
            else:
                ans = input("Pay? 1 - YES, 0 - DELETE ORDER")
                if ans.isdigit() and int(ans) == 1:
                    payment(username, orderID)
                elif ans.isdigit() and int(ans) == 0:
                    deleteOrder(orderID, username)
                    startup()

def shopping(username):
    operation = input("Do you want to order some sushi? 0 - NO, 1- YES\n")
    if operation.isdigit() and int(operation) == 1:
        printSushiSet()
        orderID = createOrder(username)
        selectSushi(username, orderID) 

def getInfoUser(userID):
    print("---USER INFO---")
    print("Your username is ", client.hget(userID, 'username'))
    print("Your userID is " , userID)
    print("You have", client.hget(userID, 'ricepoints'), " ricePoints" )
    print("---------------")

def registerNewClient(username, password):
    if check(username) == 1:
        print("ERROR - user already exists, redirecting to login")
        logIn(username, password)
        return 
    client.incr("userNum")
    userNum = client.get('userNum')
    userID = "user" + str(userNum) 
    registerUsers(userID, username)   
    client.hset(userID, 'username', username)
    client.hset(userID, 'password', password)
    client.hset(userID, 'ricepoints', 15)
    print("REGISTRATION SUCCESSFULL")
    getInfoUser(userID)
    return username
    
def logIn(username, password):
    if check(username) == 0:
        print("ERROR - user does not exist, redirecting to RREGISTER")  
        registerNewClient(username, password)     
        return   
    userID = client.get(username)
    print(client.hget(userID, 'password'))
    if password == client.hget(userID, 'password'):
        print("Login successful!!!")
        return username
    else:
        logIn(username, input("Incorrect password, try again: ")) 

def startup():
    operation = input("Press 1 to see list of sushi, 2 to order sushi, 3 to see information about your balace and shoppint cart, 4 to input new sushi, 0 TO EXIT\n ")
    
    # list all sushi types
    if operation.isdigit() and int(operation) == 1:
        printSushiSet()
        startup() 

    # logIn and order
    elif operation.isdigit() and int(operation) == 2:
        reg = input("Register - press 1, login - press 2: \n")

        #registration
        if reg.isdigit() and int(reg) == 1:
            print("Registration started...\n") 
            user = registerNewClient(input("Type your username: "), input("Type your password: "))

        #login
        if reg.isdigit() and int(reg) == 2:
            print("Login started...\n") 
            user = logIn(input("Type your username: "), input("Type your password: "))

        #shopping 
        shopping(user)
        
    # get infromation about user without registration
    elif operation.isdigit() and int(operation) == 3:
        username = input("Enter username: ")
        userID = client.get(username)
        getInfoUser(userID)
    else:
        exit()

print("-------------------------------------------------------------------------------------------------------------")
print("Welcome to the Sushi Bar! It is the place where you can order sushi with our brand new currency: RicePoints.")
print("Every new user gets 15 RicePoints for free! Once you spend them, sadly, you wont be able to order ever again.")
print("-------------------------------------------------------------------------------------------------------------")
startup()


""" print("Register new client")
registerNewClient(input("Type your name: "), input("Type your surename: ")) """

""" print(client.keys("*sushi*")) """



""" print("Input new sushi")
newSushiInput(input("Sushi name: "), input("Sushi count: "))
"""  
""" print(client.lrange('sushi', 0, -1))  """

# get a value
""" value = client.get('test-key')
    print(value) """