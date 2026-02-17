OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
rx(pi/4) q[0];
ry(pi/2) q[0];
rz(3*pi/4) q[0];
p(pi) q[0];
rx(2*pi) q[0];
