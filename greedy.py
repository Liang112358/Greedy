import numpy as np
import random
import math
from typing import Tuple
from Objects import*



#贪婪算法
def greedy_offloading_algorithm(vehicles, base_station):
    
    total_delay = 0
    total_energy = 0
    total_success_vehicle = 0
     
    # # 1. 选择头部车辆:
    # head_vehicle = select_head_vehicle(vehicles)
 
    # 2. 初始化任务卸载决策，好像没有意义
    offloading_decisions = {v.id: [random.choice([0, 1, 2]) for _ in range(6)] for v in vehicles} 

    # 3. 执行贪婪算法优化任务卸载决策
    Position=[]
    for vehicle in vehicles:
        success_tasks = 0
        for task_index in task_order(vehicle):
            task = vehicle.tasks[task_index]
            best_decision = None
            best_cost = float('inf')

            for decision in range(2):
                if decision == 0:  # 本地处理
                    delay_0 = computing_delay(task.computing_size, vehicle.computing_capacity)
                    energy_0 = computing_energy(task.computing_size, vehicle.computing_capacity, vehicle.computing_energy_cost)
                    future_position_x_0 = vehicle.position[0] + vehicle.speed * delay_0     #计算车辆位置，并未更新
                    
                    # # 更新车辆资源(不需要)
                    # vehicle.tasks[i].is_being_processed_locally = True
                    # vehicle.update_resource()
                # elif decision == 1:  # 卸载到头部车辆
                #     rate = head_vehicle.transmission_rate_V2V
                #     delay += transmission_delay(task.data_size, rate) + computing_delay(task.computing_size, head_vehicle.computing_capacity)
                #     energy += transmission_energy(task.data_size, rate, vehicle.transmission_energy_cost_V2V) + computing_energy(task.computing_size, head_vehicle.computing_capacity, head_vehicle.computing_energy_cost)
                #     # 更新车辆资源(头部车辆需要更新资源)
                #     vehicle.tasks[task_index].is_being_processed_locally = True
                #     vehicle.update_resource()
                
                    ### 计算任务完成率
                    if delay_0 > task.time_limit:
                        success_rate_0 = 0.0001 #成功率不能为0做分母，故设置成一个极小的数
                    else: success_rate_0 = 1
                    #计算cost
                    cost_0 = (delay_0 * energy_0) / success_rate_0    
                    
                else:  # 卸载到基站
                    transmission_rate_V2I = Transmission_rate_V2I(loss(distance(vehicle, base_station)), h)
                    delay_1 = transmission_delay(task.data_size, transmission_rate_V2I) + computing_delay(task.computing_size, base_station.computing_capacity)
                    energy_1 = transmission_energy(task.data_size, transmission_rate_V2I, base_station.computing_capacity, vehicle.transmission_energy_cost_V2I) + computing_energy(task.computing_size, base_station.computing_capacity, base_station.computing_energy_cost)
                    future_position_x_1 = vehicle.position[0] + vehicle.speed * delay_1 #计算车辆位置
                    ### 计算任务完成率
                    if delay_1 > task.time_limit or future_position_x_1 > max_coordinate or future_position_x_1 < min_coordinate:
                        success_rate_1 = 0.0001 #成功率不能为0做分母，故设置成一个极小的数
                    else: success_rate_1 = 1
                    #计算cost
                    cost_1 = (delay_1 * energy_1) / success_rate_1
                    
                # if success_rate >= 0.01:  # 假设成功率>=0.01视为任务成功
                #     total_success_tasks += 1
                
            if cost_0 < cost_1:
                best_cost = cost_0
                best_decision = 0
                best_delay = delay_0
                best_energy = energy_0
                best_success_rate = success_rate_0
                #更新车辆位置
                vehicle.position = (future_position_x_0, vehicle.position[1])
                # 更新车辆资源(真正决定本地处理之后才能更新)
                #有待补充
            else: 
                best_cost = cost_1
                best_decision = 1
                best_delay = delay_1
                best_energy = energy_1
                best_success_rate = success_rate_1
                #更新车辆位置
                vehicle.position = (future_position_x_1, vehicle.position[1])
                # 更新基站资源(真正决定卸载到基站之后才能更新)
                vehicle.tasks[task_index].is_being_processed_BaseStation = True
                base_station.tasks.append(task)  # 添加任务到基站的任务列表
                base_station.update_resource()
                    
            if best_success_rate <= 0.001:
                print(f"车辆{vehicle.id}的任务{task_index}无法被成功处理！")
            
            #把时延、能耗和任务成功率累加起来    
            total_delay += best_delay
            total_energy += best_energy 
            success_tasks += best_success_rate     
            offloading_decisions[vehicle.id][task_index] = best_decision
            
        if success_tasks == 6:
            total_success_vehicle += 1
        
        Position.append(vehicle.position)

    return offloading_decisions, total_delay, total_energy, total_success_vehicle, Position



##################
###### 示例：

min_coordinate = - (math.sqrt(3) * 100)   #假设基站位置为（0，0），最小坐标与最大坐标反映了基站的通信范围
max_coordinate =  math.sqrt(3) * 100
# 向下取整和向上取整
min_coordinate_int = math.floor(min_coordinate)
max_coordinate_int = math.ceil(max_coordinate)

min_speed = 100/9  #假设车辆的最小速度为(100/9) m/s，最大速度为(150/9) m/s
max_speed = 150/9

# 创建一些示例车辆、基站和任务
base_station = BaseStation(position=(0,0), resource=100, computing_capacity=8*(10**8), computing_energy_cost=48400*(10**(-28)))

vehicles = [Vehicle(id=i, 
                    position= (random.randint(min_coordinate_int, max_coordinate_int), random.randint(min_coordinate_int, max_coordinate_int)),
                    speed = round(random.uniform(min_speed, max_speed), 2),
                    resource=random.randint(20, 50),
                    tasks=[
                        Task(priority=1, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000)),
                        Task(priority=2, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000)),
                        Task(priority=3, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000)),
                        Task(priority=4, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000)),
                        Task(priority=5, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000)),
                        Task(priority=6, data_size=round(random.uniform(1, 10), 2), time_limit=round(random.uniform(2, 10), 4), computing_size=random.randint(500, 1000))
                    ], 
                    computing_capacity=random.randint(10**6, 2.5*(10**8)), 
                    computing_energy_cost=144*(10**(-28)), # 电容*电压的平方
                    transmission_energy_cost_V2I=484*(10**(-26)),  # 电容*电压的平方
                    transmission_energy_cost_V2V=144*(10**(-28)))
            for i in range(8)]


# 应用贪婪算法
offloading_decisions, total_delay, total_energy, total_success_vehicle, Position = greedy_offloading_algorithm(vehicles, base_station)
total = total_energy* total_delay* 10 /total_success_vehicle

# 输出任务卸载决策
for vehicle_id, decisions in offloading_decisions.items():
    print(f"Vehicle ID {vehicle_id}: {decisions}")

# print(f"头部车辆为：车辆{head_vehicle.id}")
print(f"总时延为：{total_delay}，总能耗为：{total_energy}，任务成功率为：{total_success_vehicle / len(vehicles)}")
print(f"总目标函数值为：{total}")
print(f"车辆位置为：{Position}")

