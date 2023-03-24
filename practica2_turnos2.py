"""
Solution to the one-way tunnel
Irma Alonso Sánchez, versión en la que se garantiza la seguridad y que no hay inanición.
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 50
NPED = 10
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.numpedpas=Value('i',0) #numero de peatones cruzando
        self.numcarnpas=Value('i',0) #numero de coches del norte cruzando
        self.numcarspas=Value('i',0) #numero de coches del sur cruzando
        
        self.carswait=Value('i',0)  #numero de coches del sur esperando
        self.carnwait=Value('i',0) #numero de coches del norte esperando
        self.pedwait=Value('i',0) #numero de peatones esperando
        
        self.turn = Value('i', -1)
        #turn 0 para coches del sur
        #turn 1 para coches del norte
        #turn 2 para peatones
        #turn -1 para todos
        
        self.no_car_s_ped = Condition(self.mutex) #pueden pasar los que van al norte
        self.no_car_n_ped = Condition(self.mutex)#pueden pasar los que van al sur
        self.no_car_s_n = Condition(self.mutex)#pueden pasar peatones
        
    def are_no_car_s_ped(self): #True si pueden pasar los del norte
    	return self.numcarspas.value==0 and self.numpedpas.value==0 and (self.turn.value == 1 or self.turn.value == -1 )
    def are_no_car_n_ped(self):#True si pueden pasar los del sur
    	return self.numcarnpas.value==0 and self.numpedpas.value==0 and (self.turn.value == 0 or self.turn.value == -1 )
    def are_no_car_s_n(self):#True si pueden pasar los peatones
    	return self.numcarspas.value==0 and self.numcarnpas.value==0 and (self.turn.value == 2 or self.turn.value == -1 )

    def wants_enter_car(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        if direction==1: 
        	self.carswait.value +=1   	
        	self.no_car_n_ped.wait_for(self.are_no_car_n_ped)
        	self.carswait.value -=1        	
        	self.numcarspas.value +=1
        else:
        	self.carnwait.value +=1
        	self.no_car_s_ped.wait_for(self.are_no_car_s_ped)
        	self.carnwait.value -=1
        	self.numcarnpas.value +=1
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        if direction==1: 
        	self.numcarspas.value -=1
        	
        	if self.carnwait.value>2:
        		self.turn.value=1
        	elif self.pedwait.value>2:
        		self.turn.value=2
        	else: #self.carswait.value==0:
        		self.turn.value=-1
        	
        	if self.numcarspas.value==0:
        		self.no_car_s_ped.notify_all()
        		self.no_car_s_n.notify_all()
        else:
        	self.numcarnpas.value -=1
        	
        	if self.carswait.value>2:
        		self.turn.value=0
        	elif self.pedwait.value>2:
        		self.turn.value=2
        	else:
        		self.turn.value=-1
        	
        	if self.numcarnpas.value==0:
        		self.no_car_n_ped.notify_all()
        		self.no_car_s_n.notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.pedwait.value +=1
        self.no_car_s_n.wait_for(self.are_no_car_s_n)
        self.pedwait.value -=1
        self.numpedpas.value +=1
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.numpedpas.value -=1
        
        if self.carnwait.value>2:
        	self.turn.value=1
        elif self.carswait.value>2:
        	self.turn.value=0
        else: #self.pedwait.value==0:
        	self.turn.value=-1
        	
        if self.numpedpas.value==0:
        		self.no_car_s_ped.notify_all()
        		self.no_car_n_ped.notify_all()
        
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    #time.sleep(0.5)
    time.sleep(random.uniform(TIME_IN_BRIDGE_CARS[1],TIME_IN_BRIDGE_CARS[0]))
    
def delay_car_south() -> None:
    #time.sleep(0.5)
    time.sleep(random.uniform(TIME_IN_BRIDGE_CARS[1],TIME_IN_BRIDGE_CARS[0]))

def delay_pedestrian() -> None:
    #time.sleep(1)
    time.sleep(random.uniform(TIME_IN_BRIDGE_PEDESTRIAN[1],TIME_IN_BRIDGE_PEDESTRIAN[0]))


def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")
   #print("FIN COCHE",cid)

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")
    #print("FIN PEATON ",pid)



def gen_pedestrian(monitor: Monitor) -> None:
	pid = 0
	plst = []
	for _ in range(NPED):
		pid += 1
		p = Process(target=pedestrian, args=(pid, monitor))
		p.start()
		plst.append(p)
		time.sleep(random.expovariate(1/TIME_PED))
	
	
	for p in plst:
		p.join()

def gen_cars(monitor) -> Monitor:
    cid = 0
    plst = []
    for _ in range(NCARS):
        direction = NORTH if random.randint(0,1)==1  else SOUTH
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_CARS))
     
    
    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars = Process(target=gen_cars, args=(monitor,))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars.start()
    gped.start()
    gcars.join()
    gped.join()


if __name__ == '__main__':
    main()
