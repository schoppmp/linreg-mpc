function [X,Y] = cgdscl(A,b,it) %#codegen
	d = size(A,2);

	Abar = zeros(d,d);
	bbar = zeros(d,1);
	M = zeros(d,d);
	nb = 0;

	X = zeros(d,it);
	Y = zeros(d,it);

	M(:) = diag(sqrt(abs(A)*ones(d,1)).^(-1));
	Abar(:) = M*A*M;
	%nb(:) = sqrt(b'*b);
    nb(:) = 1;
	bbar(:) = M*b/nb;

	Y(:) = cgd2(Abar,bbar,it);
	X(:) = nb*M*Y;

