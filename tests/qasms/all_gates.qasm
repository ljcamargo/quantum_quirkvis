OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[2] c;

h q[0];
x q[1];
y q[2];
z q[0];
s q[1];
t q[2];

barrier q;

cx q[0], q[1];
swap q[1], q[2];
cz q[0], q[2];

barrier q;

rx(pi/2) q[0];
ry(pi/4) q[1];
rz(pi) q[2];

barrier q;

c[0] = measure q[0];
measure q[1];
measure q[2];
