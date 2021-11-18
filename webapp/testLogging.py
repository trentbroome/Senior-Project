import logging 

logging.basicConfig(filename="user.log", 
					format='%(message)s'
                )

#Let us Create an object 
logger=logging.getLogger() 

#Now we are going to Set the threshold of logger to DEBUG 
logger.setLevel(logging.DEBUG)

logger.info( + " " +  name + " " + userType)