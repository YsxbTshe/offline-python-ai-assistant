# -*- coding: utf-8 -*-
# 输入校验和异常处理
try:
    # 从键盘读取一行输入
    user_input = input("请输入一行空格分隔的整数：")

    # 检查输入是否为空行
    if not user_input.strip():
        print("输入不能为空，请重新输入。")
        exit()

    # 将输入字符串按空格分割成列表
    numbers = user_input.split()

    # 统计偶数个数
    even_count = 0
    for num in numbers:
        # 尝试将字符串转换为整数
        try:
            num = int(num)
            # 检查是否为偶数
            if num % 2 == 0:
                even_count += 1
        except ValueError:
            # 如果转换失败，说明输入不是整数
            print(f"输入 {num} 不是有效的整数，请重新输入。")
            exit()

    # 输出偶数个数
    print(f"偶数的个数：{even_count}")
except KeyboardInterrupt:
    print("\n用户中断输入，程序退出。")
