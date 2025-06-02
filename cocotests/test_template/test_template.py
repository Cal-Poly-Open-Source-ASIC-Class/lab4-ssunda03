import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge,Timer

async def start_clocks(dut, w_per=7, r_per=13):
    cocotb.start_soon(Clock(dut.i_wclk, w_per, units="ns").start())
    cocotb.start_soon(Clock(dut.i_rclk, r_per, units="ns").start())

async def wr_clk_edge_p(dut):
    await RisingEdge(dut.i_wclk)

async def rd_clk_edge_p(dut):
    await RisingEdge(dut.i_rclk)

async def clk_edge_p(dut):
    await wr_clk_edge_p(dut)
    await rd_clk_edge_p(dut)

async def wr_clk_edge_n(dut):
    await FallingEdge(dut.i_wclk)

async def rd_clk_edge_n(dut):
    await FallingEdge(dut.i_rclk)

async def clk_edge_n(dut):
    await wr_clk_edge_n(dut)
    await rd_clk_edge_n(dut)
    
async def reset_dut(dut):
    await start_clocks(dut)
    
    await wr_clk_edge_n(dut)
    dut.i_wr.value = 0
    dut.i_wrst_n.value = 0
    dut.i_wdata.value = 0
    
    await rd_clk_edge_n(dut)
    dut.i_rd.value = 0
    dut.i_rrst_n.value = 0

    await wr_clk_edge_n(dut)
    dut.i_wrst_n.value = 1
    
    await rd_clk_edge_n(dut)
    dut.i_rrst_n.value = 1
    
    await clk_edge_p(dut)
    

async def write(dut, val):
    while dut.o_wfull.value:
        await wr_clk_edge_p(dut)

    await wr_clk_edge_n(dut)
    dut.i_wdata.value = val
    dut.i_wr.value = 1
    
    await wr_clk_edge_p(dut)
    await wr_clk_edge_n(dut)

    dut.i_wr.value = 0
    await wr_clk_edge_p(dut)

async def read(dut):
    while dut.o_rempty.value:
        await rd_clk_edge_p(dut)

    await rd_clk_edge_n(dut)
    dut.i_rd.value = 1
    await rd_clk_edge_n(dut)
    dut.i_rd.value = 0
    data = int(dut.o_rdata.value)
    await rd_clk_edge_n(dut)
    dut.i_rd.value = 0
    await rd_clk_edge_p(dut)

    return data

async def check_value(dut, actual, expected, num):
    assert actual == expected, f"{num} --> Actual: {actual}, Expected: {expected}"


@cocotb.test()
async def test_fill(dut):
    await reset_dut(dut)

    width = 32
    payload_list = []
    while not dut.o_wfull.value:
        payload = random.randint(0, 2 ** width - 1)
        payload_list.append(payload)
        await write(dut, payload)
    print(len(payload_list))
    
    i = 0
    while not dut.o_rempty.value:
        data = await read(dut)
        await check_value(dut, data, payload_list[i], i)
        i += 1
    print(i)
    await clk_edge_p(dut)

@cocotb.test()
async def test_alternate_fill(dut):
    await reset_dut(dut)

    width = 32
    payload_list = []
    i = 0
    while not dut.o_wfull.value:
        for _ in range(1 << i):
            if not dut.o_wfull.value:
                payload = random.randint(0, 2 ** width - 1)
                payload_list.append(payload)
                await write(dut, payload)
            else:
                break
        data = await read(dut)
        await check_value(dut, data, payload_list[i], i)
        i += 1
            