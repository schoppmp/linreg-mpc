function [X,P,G] = cgdfp2(A,b,it,T) %#codegen
	d = size(A,2);
	X = cast(zeros(d,it),'like',T);
	P = cast(zeros(d,it),'like',T);
	G = cast(zeros(d,it),'like',T);
	x = cast(zeros(d,1),'like',T);
	p = cast(zeros(d,1),'like',T);
	g = cast(zeros(d,1),'like',T);
	%pscl = cast(zeros(d,1),'like',T);
	%xupdt = cast(zeros(d,1),'like',T);
	%pupdt = cast(zeros(d,1),'like',T);
	%ng = cast(0,'like',T);
	%ngnew = cast(0,'like',T);
	q = cast(0,'like',T);
	eta = cast(0,'like',T);
	gamma = cast(0,'like',T);
	tmp = cast(0,'like',T);
	p(:) = A*x - b;
	g(:) = p;
	%ng(:) = g'*g;
	for i = 1:it
		display(sprintf('===== Iteration: %d =====',i));
		%pscl(:) = p*d;
		q(:) = p'*A*p;    
		eta(:) = (g/q)'*g;
		x(:) = x - eta*p;
		g(:) = A*x - b;
		%ngnew(:) = g'*g;
		gamma(:) = (g/eta)'*(g/q);
		p(:) = g + gamma*p;
		%ng(:) = ngnew;
		X(:,i) = x;
		P(:,i) = p;
		G(:,i) = g;
	end;

