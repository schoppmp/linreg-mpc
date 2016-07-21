function [alpha,beta,Q] = lanczos1(A,q1,it) %#codegen
	% Efficient Lanczos (10.3.1) from MC 4th ed.
	n = size(A,1);

	Q = zeros(n,it);
	w = zeros(n,1);
	v = zeros(n,1);
	alpha = zeros(it,1);
	beta = zeros(it-1,1);
	t = 0;

	w(:) = q1;
	Q(:,1) = q1;
	v(:) = A*w;
	alpha(1) = w'*v;
	v(:) = v - alpha(1)*w;

	for k = 2:it
        beta(k-1) = sqrt(v'*v);
		for i = 1:n	
			t = w(i);
			w(i) = v(i)/beta(k-1);
			v(i) = -beta(k-1)*t;
		end;
		v(:) = v + A*w;
		alpha(k) = w'*v;
		v(:) = v - alpha(k)*w;
		Q(:,k) = w;
	end;

