import sys
import os
import pytest
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from core.ladder_backend.ladder_compile import LadderCompile, ExistInfo
from core.ladder_backend.ladder_backend import LadderCommand, LadderGroup, LadderComponents, ElementClass

# 配置日志
from loguru import logger
import logging
import sys

# 移除默认的日志处理器并添加新的
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level="DEBUG")

def test_element_exist():
    """测试_element_exist方法"""
    logger.info("开始测试_element_exist方法")
    compiler = LadderCompile()
    
    # 测试(0, 0)位置的元素（左上角）
    logger.debug("测试(0, 0)位置的元素（左上角）")
    exist_info = compiler._element_exist((3, 3), (0, 0))
    assert exist_info.top == False
    assert exist_info.buttom == True
    assert exist_info.left == False
    assert exist_info.right == True
    
    # 测试(1, 1)位置的元素（中间）
    logger.debug("测试(1, 1)位置的元素（中间）")
    exist_info = compiler._element_exist((3, 3), (1, 1))
    assert exist_info.top == True
    assert exist_info.buttom == True
    assert exist_info.left == True
    assert exist_info.right == True
    
    # 测试(2, 2)位置的元素（右下角）
    logger.debug("测试(2, 2)位置的元素（右下角）")
    exist_info = compiler._element_exist((3, 3), (2, 2))
    assert exist_info.top == True
    assert exist_info.buttom == False
    assert exist_info.left == True
    assert exist_info.right == False
    logger.info("_element_exist方法测试完成")

def test_connect_rules_normal_open():
    """测试正常开触点连接规则"""
    logger.info("开始测试正常开触点连接规则")
    compiler = LadderCompile()
    
    # 创建测试用元件
    component = ElementClass("comp1", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)
    
    # 创建一个1x3的梯形图布局
    ladder_info = {"comp0": ElementClass("comp0", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0),
                   "comp1": component,
                   "comp2": ElementClass("comp2", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)}
    
    ladder_pos = [["comp0", "comp1", "comp2"]]
    
    # 测试合法连接
    logger.debug("测试合法连接")
    result, msg = compiler._connect_rules((0, 1), component, (1, 3), ladder_info, ladder_pos)
    logger.debug(f"合法连接测试结果: {result}, 消息: {msg}")
    assert result == True
    assert msg == ""
    
    # 检查链表结构
    prev_component = ladder_info["comp0"]
    next_component = ladder_info["comp2"]
    assert component.prev[0] == prev_component
    assert component.next[0] == next_component
    logger.debug(f"链表结构检查: prev={component.prev[0].id}, next={component.next[0].id}")
    
    # 测试缺少右侧元件的情况（应该报错）
    logger.debug("测试缺少右侧元件的情况")
    ladder_pos_invalid = [["comp0", "comp1"]]
    ladder_info_invalid = {"comp0": ElementClass("comp0", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0),
                           "comp1": component}
    result, msg = compiler._connect_rules((0, 1), component, (1, 2), ladder_info_invalid, ladder_pos_invalid)
    logger.debug(f"缺少右侧元件测试结果: {result}, 消息: {msg}")
    assert result == False
    assert "[NORMAL_OPEN/NORMAL_CLOSED]: 右方不存在元素/线圈" in msg
    logger.info("正常开触点连接规则测试完成")

def test_connect_rules_coil():
    """测试线圈连接规则"""
    logger.info("开始测试线圈连接规则")
    compiler = LadderCompile()
    
    # 创建测试用元件
    component = ElementClass("coil1", (0, 0, 10, 10), LadderComponents.COIL, 0)
    
    # 创建一个合法的梯形图布局
    ladder_info = {"comp0": ElementClass("comp0", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0),
                   "coil1": component}
    
    ladder_pos = [["comp0", "coil1"]]
    
    # 测试合法连接
    logger.debug("测试合法连接")
    result, msg = compiler._connect_rules((0, 1), component, (1, 2), ladder_info, ladder_pos)
    logger.debug(f"合法连接测试结果: {result}, 消息: {msg}")
    assert result == True
    assert msg == ""
    
    # 检查链表结构
    prev_component = ladder_info["comp0"]
    assert component.prev[0] == prev_component
    assert len(component.next) == 0
    logger.debug(f"线圈链表结构检查: prev={component.prev[0].id}, next数量={len(component.next)}")
    
    # 测试右侧有元件的情况
    logger.debug("测试右侧有元件的情况")
    ladder_pos_invalid = [["comp0", "coil1", "comp2"]]
    ladder_info_invalid = {"comp0": ElementClass("comp0", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0),
                           "coil1": component,
                           "comp2": ElementClass("comp2", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)}
    
    result, msg = compiler._connect_rules((0, 1), component, (1, 3), ladder_info_invalid, ladder_pos_invalid)
    logger.debug(f"右侧有元件测试结果: {result}, 消息: {msg}")
    assert result == False
    assert "[COIL]: 右方存在元素" in msg
    logger.info("线圈连接规则测试完成")

def test_structure_compile():
    """测试_structure_compile方法"""
    logger.info("开始测试_structure_compile方法")
    compiler = LadderCompile()
    
    # 创建梯形图指令
    ladder_command = LadderCommand()
    
    # 添加元件
    logger.debug("添加元件")
    comp1 = ElementClass("comp1", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)
    comp2 = ElementClass("comp2", (10, 0, 20, 10), LadderComponents.COIL, 0)
    
    ladder_command.add_component(comp1)
    ladder_command.add_component(comp2)
    
    # 手动设置位置以确保正确排序
    ladder_command.components_location = [["comp1", "comp2"]]
    
    # 测试编译
    logger.debug("执行结构编译")
    result = compiler._structure_compile(ladder_command)
    # 应该返回元组(legal, debug_info)
    logger.debug(f"结构编译结果: {result}")
    
    # 检查链表结构
    assert comp1.next[0] == comp2
    assert comp2.prev[0] == comp1
    logger.debug(f"完整链表结构检查: {comp1.id} -> {comp2.id}")
    
    assert result is None or (isinstance(result, tuple) and len(result) == 2)
    logger.info("_structure_compile方法测试完成")

def test_info_compile():
    """测试_info_compile方法"""
    logger.info("开始测试_info_compile方法")
    compiler = LadderCompile()
    
    # 初始化必要的属性
    compiler.registed_components = {}
    compiler.input_device = set()
    compiler.output_device = []
    
    # 创建梯形图指令
    ladder_command = LadderCommand()
    
    # 添加元件
    logger.debug("添加元件")
    comp1 = ElementClass("comp1", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)
    coil1 = ElementClass("coil1", (10, 0, 20, 10), LadderComponents.COIL, 0)
    
    ladder_command.add_component(comp1)
    ladder_command.add_component(coil1)
    
    # 手动设置位置以确保正确排序
    ladder_command.components_location = [["comp1", "coil1"]]
    
    # 创建连接信息
    logger.debug("创建连接信息")
    connect_info = [
        {
            "id": "comp1",
            "name": "sensor1",
            "properties": {
                "option": "sensor_option"
            }
        },
        {
            "id": "coil1", 
            "name": "device1",
            "properties": {
                "option": "device_option"
            }
        }
    ]
    
    # 测试编译
    logger.debug("执行信息编译")
    result = compiler._info_compile(connect_info, ladder_command)
    # 应该返回元组(legal, debug_info)
    logger.debug(f"信息编译结果: {result}")
    
    # 检查属性设置
    assert "sensor_option" in comp1.sensor
    assert "device_option" in coil1.device
    logger.debug(f"属性设置检查: comp1.sensor={comp1.sensor}, coil1.device={coil1.device}")
    
    assert result is None or (isinstance(result, tuple) and len(result) == 2)
    logger.info("_info_compile方法测试完成")
def test_ladder_compile_call():
    """测试LadderCompile的__call__方法"""
    logger.info("开始测试LadderCompile的__call__方法")
    compiler = LadderCompile()
    
    # 创建梯形图组
    logger.debug("创建梯形图组")
    ladder_group = LadderGroup()
    ladder_command = LadderCommand()
    
    # 添加元件
    logger.debug("添加元件")
    comp1 = ElementClass("comp1", (0, 0, 10, 10), LadderComponents.NORMAL_OPEN, 0)
    coil1 = ElementClass("coil1", (10, 0, 20, 10), LadderComponents.COIL, 0)
    
    ladder_command.add_component(comp1)
    ladder_command.add_component(coil1)
    
    # 手动设置位置以确保正确排序
    ladder_command.components_location = [["comp1", "coil1"]]
    
    ladder_group.add_ladder(0, ladder_command)
    
    # 创建连接信息
    logger.debug("创建连接信息")
    connect_info = {
        0: [
            {
                "id": "comp1",
                "name": "sensor1",
                "properties": {
                    "option": "sensor_option"
                }
            },
            {
                "id": "coil1",
                "name": "device1", 
                "properties": {
                    "option": "device_option"
                }
            }
        ]
    }
    
    # 保存原始元件的引用用于比较
    original_comp1 = comp1
    original_coil1 = coil1
    
    # 测试编译
    logger.debug("执行完整编译流程")
    result = compiler(ladder_group, connect_info)
    # 应该返回编译结果
    logger.debug(f"完整编译结果: {result}")
    
    # 检查编译结果
    if result:
        assert result.get("success", False) == True
        logger.debug("编译成功")
    
    # 由于使用了深拷贝，原始元件不会被修改，需要从编译结果中获取元件
    compiled_group = result.get("compiled_group")
    compiled_ladder_command = compiled_group.group[0]
    compiled_comp1 = compiled_ladder_command.components_dict["comp1"]
    compiled_coil1 = compiled_ladder_command.components_dict["coil1"]
    
    # 检查链表和属性（应该在编译后的副本中检查）
    assert compiled_comp1.next[0] == compiled_coil1
    assert compiled_coil1.prev[0] == compiled_comp1
    assert "sensor_option" in compiled_comp1.sensor
    assert "device_option" in compiled_coil1.device
    logger.debug(f"完整链表结构检查: {compiled_comp1.id} -> {compiled_coil1.id}")
    logger.debug(f"属性设置检查: compiled_comp1.sensor={compiled_comp1.sensor}, compiled_coil1.device={compiled_coil1.device}")
    
    # 确保原始元件没有被修改（深拷贝的效果）
    assert len(original_comp1.next) == 0
    assert len(original_coil1.prev) == 0
    assert not hasattr(original_comp1, 'sensor') or "sensor_option" not in original_comp1.sensor
    assert not hasattr(original_coil1, 'device') or "device_option" not in original_coil1.device
    logger.debug("确认原始元件未被修改，验证了深拷贝功能")
    
    assert result is None or isinstance(result, dict)
    logger.info("LadderCompile的__call__方法测试完成")

# 添加主程序入口
if __name__ == "__main__":
    logger.info("开始运行梯形图编译器单元测试")
    
    try:
        # 运行所有测试
        test_element_exist()
        logger.info("element_exist 测试通过")
        
        test_connect_rules_normal_open()
        logger.info("connect_rules_normal_open 测试通过")
        
        test_connect_rules_coil()
        logger.info("connect_rules_coil 测试通过")
        
        test_structure_compile()
        logger.info("structure_compile 测试通过")
        
        test_info_compile()
        logger.info("info_compile 测试通过")
        
        test_ladder_compile_call()
        logger.info("ladder_compile_call 测试通过")
        
        logger.info("所有测试已完成")
    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        raise