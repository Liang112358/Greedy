import numpy as np
import random
import math
from typing import Tuple


#车辆
class Vehicle:
    def __init__(self, id, position: Tuple[float, float], speed, resource, tasks, computing_capacity, 
                 computing_energy_cost, transmission_energy_cost_V2I, transmission_energy_cost_V2V):
        self.id = id
        self.position = position
        self.speed = speed
        self.resource = resource
        self.tasks = tasks
        self.computing_capacity = computing_capacity
        self.computing_energy_cost = computing_energy_cost
        self.transmission_energy_cost_V2I = transmission_energy_cost_V2I
        self.transmission_energy_cost_V2V = transmission_energy_cost_V2V
        
    #更新坐标    
    def update_position(self, time: float):
        #如果假设直线行驶，那么车辆只需更新x坐标即可
        new_position_x = self.position[0] + self.speed * time
        new_position_y = self.position[1]
        self.position = (new_position_x, new_position_y)
        
    #更新资源    
    def update_resource(self):
        #任务占用的资源量怎么算？此处先用task.data_size代替
        resource_used = sum(task.data_size for task in self.tasks if task.is_being_processed_locally) 
        self.resource -= resource_used

# #头部车辆
# class HeadVehicle(Vehicle):
#     def __init__(self, id, position: Tuple[float, float], speed, resource, tasks, computing_capacity, 
#                  computing_energy_cost, transmission_rate_V2V, transmission_rate_V2I, transmission_energy_cost_V2I, 
#                  transmission_energy_cost_V2V):
#             super().__init__(self, id, position, speed, resource, tasks, computing_capacity, 
#                  computing_energy_cost, transmission_rate_V2V, transmission_rate_V2I, transmission_energy_cost_V2I,
#                  transmission_energy_cost_V2V)

#     def update(self, current_time):
#         if current_time - self.last_updated_time > some_interval:
#             # 更新头部车辆的一些属性或状态
#             self.last_updated_time = current_time
     
#基站
class BaseStation:
    def __init__(self, position: Tuple[float, float], resource, computing_capacity, computing_energy_cost):
        self.position = position
        self.resource = resource   
        self.computing_capacity = computing_capacity
        self.computing_energy_cost = computing_energy_cost
        self.tasks = []  # 添加 tasks 属性    
    #更新资源    
    def update_resource(self):
        #下面的任务占用的资源量怎么算？此处先用task.data_size代替
        resource_used = sum(task.data_size for task in self.tasks if task.is_being_processed_BaseStation)
        self.resource -= resource_used
        
#任务
class Task:
    def __init__(self, priority, data_size, time_limit, computing_size):
        self.priority = priority
        self.data_size = data_size
        self.time_limit = time_limit
        self.computing_size = computing_size
        self.is_being_processed_locally = False  
        self.is_being_processed_BaseStation = False  
        self.completed = False  # 表示这个任务是否已经完成
        
#距离       
def distance(a, b):
    return math.sqrt((a.position[0] - b.position[0])**2 + (a.position[1] - b.position[1])**2)

#传输时延
def transmission_delay(data_size, rate):
    return 1.1*data_size / rate    #1.1=1+0.1, 因为回传数据的大小是上传数据量的0.1
#传输能耗
def transmission_energy(data_size, rate, capacity, energy_cost):
    return (capacity*energy_cost)* (1.1*data_size / rate)      #此处的energy_cost是电容*电压的平方,(data_size / rate)为传输时延
#计算时延
def computing_delay(computing_size, capacity):
    return computing_size / capacity
#计算能耗
def computing_energy(computing_size, capacity, energy_cost): 
    return  (capacity*energy_cost)* (computing_size / capacity) #此处的energy_cost是电容*电压的平方，(computing_size / capacity)为计算时延

###传输速率相关参数:
#信道损失
def loss(distance):
    return 10**((-63.3+17.7*math.log(distance,10))/10)
#信道衰落系数h
h= 2*math.sqrt(2*math.log(1/(1-round(random.uniform(0, 1), 2))))
#V2I传输速率
def Transmission_rate_V2I(loss, h):
    return math.log(1+(40*loss*(h**2))/(3*(10**(-13))),2)
#V2V传输速率
def Transmission_rate_V2V(loss, h):
    return math.log(1+(1.3*loss*(h**2))/(3*(10**(-13))),2)

#任务优先级——按照优先级升序排列：
def task_order(vehicle):
    return sorted(range(len(vehicle.tasks)), key=lambda i: vehicle.tasks[i].priority)

# Q-learning代码中所用的计算
def compute_cost(vehicle, base_station, task, action):
    success_rate = 1

    if action == 0:  # 本地处理
        delay = computing_delay(task.computing_size, vehicle.computing_capacity)
        energy = computing_energy(task.computing_size, vehicle.computing_capacity, vehicle.computing_energy_cost)
        future_position_x_0 = vehicle.position[0] + vehicle.speed * delay
    
        ### 计算任务完成率
        if delay > task.time_limit:
            success_rate = 0.0001 #成功率不能为0做分母，故设置成一个极小的数
        else: success_rate = 1
        # #计算cost
        # cost = (delay * energy) / success_rate   
        #更新车辆位置
        vehicle.position = (future_position_x_0, vehicle.position[1])

    else:  # 卸载到基站
        transmission_rate_V2I = Transmission_rate_V2I(loss(distance(vehicle, base_station)), h)
        delay = transmission_delay(task.data_size, transmission_rate_V2I) + computing_delay(task.computing_size, base_station.computing_capacity)
        energy = transmission_energy(task.data_size, transmission_rate_V2I, base_station.computing_capacity, vehicle.transmission_energy_cost_V2I) + computing_energy(task.computing_size, base_station.computing_capacity, base_station.computing_energy_cost)
        future_position_x_1 = vehicle.position[0] + vehicle.speed * delay
        ### 计算任务完成率
        if delay > task.time_limit or future_position_x_1 > max_coordinate or future_position_x_1 < min_coordinate:
            success_rate = 0.0001 #成功率不能为0做分母，故设置成一个极小的数
        else: success_rate = 1
        # #计算cost
        # cost = (delay * energy) / success_rate
        #更新车辆位置
        vehicle.position = (future_position_x_1, vehicle.position[1])
        # 更新基站资源(真正决定卸载到基站之后才能更新)
        vehicle.tasks[task_index].is_being_processed_BaseStation = True
        base_station.tasks.append(task)  # 添加任务到基站的任务列表
        base_station.update_resource()

    return delay, energy, success_rate





# # 选择头部车辆    ##还得每隔一段时间更新头部车辆  
# def select_head_vehicle(vehicles):
#     head_vehicle = vehicles[0]
#     distances = [distance(head_vehicle, v) for v in vehicles[1:]]  # 计算头部车辆与其他车辆的距离
#     average_distance = sum(distances) / len(distances)   # 计算平均距离
    
#     max_score = 0.5 * average_distance + 0.5 * head_vehicle.resource #权重设置为0.5, 0.5

#     for vehicle in vehicles[1:]:
#         distances = [distance(vehicle, v) for v in vehicles if v != vehicle]  # 计算当前车辆与其他车辆的距离
#         average_distance = sum(distances) / len(distances)  # 计算平均距离

#         score = 0.5 * average_distance + 0.5 * vehicle.resource
#         if score > max_score: #得分更大，就更新
#             head_vehicle = vehicle
#             max_score = score

#     return head_vehicle