function [x] = symtrisolv(alpha,beta,b) %#codegen
	n = length(alpha);
	x = zeros(n,1);
	y = zeros(n,1);
	z = zeros(n,1);
	d = zeros(n,1);
	l = zeros(n-1,1);
	t = 0;
	% Implicit LDLT of the tridiagonal given by alpha and beta
	d(1) = alpha(1);
	for k = 2:n
		l(k-1) = beta(k-1)/d(k-1);
		d(k) = alpha(k) - l(k-1)*beta(k-1);
	end;
	% Backsubstitution 1
	y(1) = b(1);
	for k = 2:n
		y(k) = b(k) - l(k-1)*y(k-1);
	end;
	% Backsubstitution 2
	for k = 1:n
		z(k) = y(k)/d(k);
	end;
	% Backsubstitution 3
	x(n) = z(n);
	for k = n-1:-1:1
		x(k) = z(k) - l(k)*x(k+1);
	end;

