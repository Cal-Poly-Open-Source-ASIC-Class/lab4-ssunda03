module asyncfifo (
    input wire i_wclk,
    input wire i_rclk,

    input wire i_wrst_n,
    input wire i_rrst_n,

    input wire i_wr,
    input wire i_rd,

    input wire [31:0] i_wdata,
    output reg [31:0] o_rdata,

    output wire o_wfull,
    output wire o_rempty
);

    parameter	DATAW = 32;
    parameter	ADRW =  8;

    reg  [ADRW:0] wbin;
    reg  [ADRW:0] wgray;
    wire [ADRW:0] wbin_next;
    wire [ADRW:0] wgray_next;
    
    reg  [ADRW:0] rbin;
    reg  [ADRW:0] rgray;
    wire [ADRW:0] rbin_next;
    wire [ADRW:0] rgray_next;

    logic  [31:0] mem [0:(1 << ADRW)-1];

    reg [ADRW:0] rq1_wgray;
    reg [ADRW:0] rq2_wgray;
    reg [ADRW:0] wq1_rgray;
    reg [ADRW:0] wq2_rgray;

    wire we, re;
    
    initial begin
        wbin = 0;
        wgray = 0;
        rbin = 0;
        rgray = 0;

        rq1_wgray = 0;
        rq2_wgray = 0;
        wq1_rgray = 0;
        wq2_rgray = 0;

        o_rdata = 0;

        // for (int i = 0; i < (1 << ADRW); i++) begin
        //     mem[i] = 32'b0;
        // end
    end

    
    assign o_wfull = wgray[ADRW:ADRW-1] != wq2_rgray[ADRW:ADRW-1] && wgray[ADRW-2:0] == wq2_rgray[ADRW-2:0];
    assign we = i_wr & !o_wfull;
    assign wgray_next = wbin_next ^ (wbin_next >> 1);
    assign wbin_next = wbin + {{(ADRW-1){1'b0}},we};
    always_ff @( posedge i_wclk ) begin
        if (!i_wrst_n) begin
            wbin <= 0;
            wgray <= 0;
        end
        else begin
            wbin <= wbin_next;
            wgray <= wgray_next;
        end

        if (we) begin
            mem[wbin[ADRW-1:0]] <= i_wdata;
        end
    end

    // write domain --> read domain
    always_ff @( posedge i_rclk ) begin
        if (!i_rrst_n) begin
            { rq2_wgray, rq1_wgray } <= 0;
        end
        else begin
            { rq2_wgray, rq1_wgray } <= { rq1_wgray, wgray };
        end
    end

    assign	o_rempty = (rq2_wgray == rgray);
    assign re = i_rd & !o_rempty;
    assign rgray_next = rbin_next ^ (rbin_next >> 1);
    assign rbin_next = rbin + {{(ADRW-1){1'b0}},re};
    always_ff @( posedge i_rclk ) begin
        if (!i_rrst_n) begin
            rbin <= 0;
            rgray <= 0;
        end
        else begin
            rbin <= rbin_next;
            rgray <= rgray_next; 
        end
        
        if (re) begin
            o_rdata <= mem[rbin[ADRW-1:0]];
        end
    end

    // read domain --> write domain
    always_ff @( posedge i_wclk) begin
        if (!i_wrst_n) begin
            { wq2_rgray, wq1_rgray } <= 0;
        end
        else begin
            { wq2_rgray, wq1_rgray } <= { wq1_rgray, rgray };
        end
    end
    

endmodule