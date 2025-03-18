#!/usr/bin/env python

import os
import csv
import argparse
import sys
import logging
import json
import re
from datetime import datetime

def setup_logger(verbose):
    """设置日志记录器"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def extract_energy_from_oszicar(filepath):
    """从OSZICAR文件中提取最终能量"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in reversed(lines):
                if 'F=' in line:
                    energy = float(line.split('F=')[1].split()[0])
                    return energy
    except Exception as e:
        logging.warning(f"读取{filepath}时出错: {e}")
    return None

def extract_energy_from_outcar(filepath):
    """从OUTCAR文件中提取最终能量"""
    try:
        with open(filepath, 'r') as f:
            energy = None
            for line in f:
                if "free  energy   TOTEN" in line:
                    energy = float(line.split()[-2])
            return energy
    except Exception as e:
        logging.warning(f"读取{filepath}时出错: {e}")
    return None

def extract_energy_from_vasprun(filepath):
    """从vasprun.xml文件中提取最终能量"""
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if "e_fr_energy" in line:
                    # 这是一种简单的解析方法，可能需要更健壮的XML解析
                    parts = line.split('>')
                    if len(parts) > 1:
                        energy_part = parts[1].split('<')[0]
                        return float(energy_part)
    except Exception as e:
        logging.warning(f"读取{filepath}时出错: {e}")
    return None

def get_energy(directory):
    """尝试从目录中的不同VASP输出文件中提取能量"""
    # 按优先级尝试不同文件
    extractors = {
        'OSZICAR': extract_energy_from_oszicar,
        'OUTCAR': extract_energy_from_outcar,
        'vasprun.xml': extract_energy_from_vasprun
    }
    
    for file_name, extractor in extractors.items():
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            logging.debug(f"正在从 {file_path} 中提取能量")
            energy = extractor(file_path)
            if energy is not None:
                return energy, file_name
    
    return None, None

def find_calculation_dirs(root_dir, recursive=False):
    """找到包含VASP计算结果的目录"""
    vasp_dirs = []
    
    # 定义VASP输出文件列表
    vasp_files = ['OSZICAR', 'OUTCAR', 'vasprun.xml']
    
    if recursive:
        # 递归查找所有子目录
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 检查是否有任何VASP输出文件
            if any(vasp_file in filenames for vasp_file in vasp_files):
                vasp_dirs.append(dirpath)
    else:
        # 只检查直接子目录
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isdir(item_path):
                # 检查是否有任何VASP输出文件
                if any(os.path.exists(os.path.join(item_path, vasp_file)) for vasp_file in vasp_files):
                    vasp_dirs.append(item_path)
    
    return vasp_dirs

def parse_reaction_term(term):
    """解析反应方程式中的项，如 "2H2O" 解析为 (2.0, "H2O")"""
    term = term.strip()
    if not term:
        return 0, ""
    
    # 使用正则表达式匹配系数
    match = re.match(r'^(\d*\.?\d*)([A-Za-z0-9_\.-]+)$', term)
    if match:
        coef_str, name = match.groups()
        # 如果系数为空字符串，则默认为1
        coef = float(coef_str) if coef_str else 1.0
        return coef, name
    else:
        # 没有系数，默认为1
        return 1.0, term

def calculate_reaction_energy(energies, reaction_formula):
    """计算反应能量
    
    参数:
        energies: 结构名称到能量的映射字典
        reaction_formula: 反应方程式字符串，格式如 "A + 2B -> C + 3D"
        
    返回:
        反应能量或如果无法计算则返回None
    """
    try:
        # 解析反应方程式
        if "->" in reaction_formula:
            reactants, products = reaction_formula.split("->")
        elif "=" in reaction_formula:
            reactants, products = reaction_formula.split("=")
        else:
            logging.error(f"无效的反应格式: {reaction_formula}，请使用 -> 或 = 分隔反应物和产物")
            return None
        
        # 解析反应物
        reactant_terms = reactants.strip().split("+")
        reactant_energy = 0
        for term in reactant_terms:
            coef, name = parse_reaction_term(term)
            if name:
                if name in energies:
                    reactant_energy += coef * energies[name]
                else:
                    logging.warning(f"在能量数据中找不到反应物 '{name}'")
                    return None
        
        # 解析产物
        product_terms = products.strip().split("+")
        product_energy = 0
        for term in product_terms:
            coef, name = parse_reaction_term(term)
            if name:
                if name in energies:
                    product_energy += coef * energies[name]
                else:
                    logging.warning(f"在能量数据中找不到产物 '{name}'")
                    return None
        
        # 计算反应能量：产物 - 反应物
        reaction_energy = product_energy - reactant_energy
        return reaction_energy
    
    except Exception as e:
        logging.error(f"计算反应能量时出错: {e}")
        return None

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='从VASP计算结果中提取能量数据')
    parser.add_argument('-d', '--directory', default='.', help='要扫描的根目录，默认为当前目录')
    parser.add_argument('-o', '--output', default='energies.csv', help='输出CSV文件名，默认为energies.csv')
    parser.add_argument('-r', '--recursive', action='store_true', help='递归扫描子目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('-j', '--json', help='同时保存JSON格式的能量数据')
    parser.add_argument('--reactions', help='包含反应方程式的文件，每行一个反应，格式为 "A + 2B -> C + 3D"')
    args = parser.parse_args()
    
    # 设置日志记录
    logger = setup_logger(args.verbose)
    
    # 获取指定目录
    root_dir = os.path.abspath(args.directory)
    if not os.path.isdir(root_dir):
        logger.error(f"错误：{root_dir} 不是一个有效的目录")
        sys.exit(1)
    
    logger.info(f"扫描目录: {root_dir}")
    
    # 找到包含VASP计算的目录
    calc_dirs = find_calculation_dirs(root_dir, args.recursive)
    
    if not calc_dirs:
        logger.warning(f"在 {root_dir} 中未找到包含VASP计算的目录")
        sys.exit(0)
    
    logger.info(f"找到 {len(calc_dirs)} 个可能包含VASP计算的目录")
    
    # 存储能量的字典
    energies = {}
    sources = {}
    
    # 从每个目录提取能量
    for full_path in sorted(calc_dirs):
        # 获取相对路径作为目录名
        rel_path = os.path.relpath(full_path, root_dir)
        
        energy, source_file = get_energy(full_path)
        
        if energy is not None:
            # 使用目录名（而不是完整路径）作为键
            dir_name = os.path.basename(rel_path)
            energies[dir_name] = energy
            sources[dir_name] = source_file
            logger.info(f"从 {rel_path} 的 {source_file} 提取的能量: {energy:.6f} eV")
        else:
            logger.warning(f"在 {rel_path} 中未找到可用的能量数据")
    
    if not energies:
        logger.warning("未找到任何能量数据。")
        sys.exit(0)
    
    # 输出能量数据
    energy_data = []
    for dir_name, energy in sorted(energies.items()):
        energy_data.append({
            'structure': dir_name,
            'energy': energy,
            'source': sources[dir_name]
        })
    
    # 计算反应能量（如果提供了反应文件）
    reaction_results = []
    if args.reactions and os.path.exists(args.reactions):
        logger.info(f"从 {args.reactions} 读取反应方程式")
        try:
            with open(args.reactions, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        reaction_energy = calculate_reaction_energy(energies, line)
                        
                        if reaction_energy is not None:
                            logger.info(f"反应 '{line}' 的能量变化: {reaction_energy:.6f} eV")
                            reaction_results.append({
                                'reaction': line,
                                'energy': reaction_energy
                            })
                        else:
                            logger.warning(f"无法计算反应 '{line}' 的能量")
        except Exception as e:
            logger.error(f"读取反应文件时出错: {e}")
    
    # 将能量保存到CSV
    output_file = args.output
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # 添加标题行和元数据
        writer.writerow(['# VASP能量提取结果'])
        writer.writerow(['# 创建时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['# 根目录:', root_dir])
        writer.writerow(['# 递归扫描:', 'Yes' if args.recursive else 'No'])
        writer.writerow([])
        
        writer.writerow(['结构', '能量 (eV)', '数据来源'])
        for dir_name, energy in sorted(energies.items()):
            writer.writerow([dir_name, f"{energy:.6f}", sources[dir_name]])
        
        # 如果有反应结果，也写入CSV
        if reaction_results:
            writer.writerow([])
            writer.writerow(['# 反应能量'])
            writer.writerow(['反应', '能量变化 (eV)'])
            for result in reaction_results:
                writer.writerow([result['reaction'], f"{result['energy']:.6f}"])
    
    logger.info(f"已将能量数据保存至 {output_file}")
    
    # 如果指定了JSON输出，也保存JSON格式
    if args.json:
        json_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'root_directory': root_dir,
                'recursive': args.recursive
            },
            'energies': energy_data
        }
        
        if reaction_results:
            json_data['reactions'] = reaction_results
        
        with open(args.json, 'w') as f:
            json.dump(json_data, f, indent=2)
        logger.info(f"已将能量数据以JSON格式保存至 {args.json}")
    
    # 汇总
    logger.info(f"总结: 处理了 {len(calc_dirs)} 个目录，提取了 {len(energies)} 个能量值")
    if reaction_results:
        logger.info(f"计算了 {len(reaction_results)} 个反应的能量变化")

if __name__ == "__main__":
    main()
