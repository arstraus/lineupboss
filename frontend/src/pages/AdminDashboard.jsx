import React, { useState, useEffect } from "react";
import { api } from "../services/api";

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeTab, setActiveTab] = useState("pending");
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    fetchUsers();
    fetchPendingCount();
  }, [activeTab]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      let url = `/admin/users`;
      
      if (activeTab !== "all") {
        url += `?status=${activeTab}`;
      }
      
      const response = await api.get(url);
      setUsers(response.data);
      setError("");
    } catch (err) {
      console.error("Error fetching users:", err);
      setError("Failed to load users. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const fetchPendingCount = async () => {
    try {
      const response = await api.get('/admin/pending-count');
      setPendingCount(response.data.pending_count);
    } catch (err) {
      console.error("Error fetching pending count:", err);
    }
  };

  const handleApprove = async (userId) => {
    try {
      setLoading(true);
      await api.post(`/admin/users/${userId}/approve`);
      
      // Remove from list if viewing pending users
      if (activeTab === "pending") {
        setUsers(users.filter(user => user.id !== userId));
      } else {
        // Update status if viewing all users
        setUsers(users.map(user => 
          user.id === userId ? { ...user, status: "approved" } : user
        ));
      }
      
      await fetchPendingCount();
      setSuccess(`User approved successfully`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Error approving user:", err);
      setError("Failed to approve user. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (userId, reason = "") => {
    try {
      setLoading(true);
      await api.post(`/admin/users/${userId}/reject`, { reason });
      
      // Remove from list if viewing pending users
      if (activeTab === "pending") {
        setUsers(users.filter(user => user.id !== userId));
      } else {
        // Update status if viewing all users
        setUsers(users.map(user => 
          user.id === userId ? { ...user, status: "rejected" } : user
        ));
      }
      
      await fetchPendingCount();
      setSuccess(`User rejected successfully`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Error rejecting user:", err);
      setError("Failed to reject user. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handlePromote = async (userId) => {
    try {
      setLoading(true);
      await api.put(`/admin/users/${userId}/role`, { role: 'admin' });
      
      // Update role in the list
      setUsers(users.map(user => 
        user.id === userId ? { ...user, role: "admin" } : user
      ));
      
      setSuccess(`User promoted to admin successfully`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Error promoting user:", err);
      setError("Failed to promote user. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemote = async (userId) => {
    try {
      setLoading(true);
      await api.put(`/admin/users/${userId}/role`, { role: 'user' });
      
      // Update role in the list
      setUsers(users.map(user => 
        user.id === userId ? { ...user, role: "user" } : user
      ));
      
      setSuccess(`User demoted to regular user successfully`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Error demoting user:", err);
      setError("Failed to demote user. Please try again.");
    } finally {
      setLoading(false);
    }
  };
  
  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return;
    }
    
    try {
      setLoading(true);
      await api.delete(`/admin/users/${userId}`);
      
      // Remove user from the list
      setUsers(users.filter(user => user.id !== userId));
      
      setSuccess(`User deleted successfully`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Error deleting user:", err);
      setError("Failed to delete user. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Format date helpers
  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString() + " " + date.toLocaleTimeString();
  };

  // Status badge helper
  const getStatusBadge = (status) => {
    switch (status) {
      case "pending":
        return <span className="badge bg-warning">Pending</span>;
      case "approved":
        return <span className="badge bg-success">Approved</span>;
      case "rejected":
        return <span className="badge bg-danger">Rejected</span>;
      default:
        return <span className="badge bg-secondary">{status}</span>;
    }
  };

  // Role badge helper
  const getRoleBadge = (role) => {
    switch (role) {
      case "admin":
        return <span className="badge bg-info">Admin</span>;
      case "user":
        return <span className="badge bg-secondary">User</span>;
      default:
        return <span className="badge bg-secondary">{role}</span>;
    }
  };

  if (loading && users.length === 0) {
    return <div className="text-center mt-5"><div className="spinner-border"></div></div>;
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>
          <i className="bi bi-shield-lock me-2"></i>
          Admin Dashboard
        </h2>
        {pendingCount > 0 && (
          <span className="badge bg-danger">
            {pendingCount} pending {pendingCount === 1 ? 'approval' : 'approvals'}
          </span>
        )}
      </div>
      
      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}
      
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending {pendingCount > 0 && <span className="badge bg-danger ms-1">{pendingCount}</span>}
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'approved' ? 'active' : ''}`}
            onClick={() => setActiveTab('approved')}
          >
            Approved
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'rejected' ? 'active' : ''}`}
            onClick={() => setActiveTab('rejected')}
          >
            Rejected
          </button>
        </li>
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            All Users
          </button>
        </li>
      </ul>
      
      {users.length === 0 ? (
        <div className="alert alert-info">
          No {activeTab !== 'all' ? activeTab : ''} users found.
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped table-hover">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created At</th>
                <th>Approved At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td>{user.id}</td>
                  <td>{user.email}</td>
                  <td>{getRoleBadge(user.role)}</td>
                  <td>{getStatusBadge(user.status)}</td>
                  <td>{formatDate(user.created_at)}</td>
                  <td>{formatDate(user.approved_at)}</td>
                  <td>
                    <div className="btn-group btn-group-sm">
                      {user.status === 'pending' && (
                        <>
                          <button 
                            className="btn btn-success"
                            onClick={() => handleApprove(user.id)}
                            disabled={loading}
                          >
                            <i className="bi bi-check"></i> Approve
                          </button>
                          <button 
                            className="btn btn-danger"
                            onClick={() => handleReject(user.id)}
                            disabled={loading}
                          >
                            <i className="bi bi-x"></i> Reject
                          </button>
                        </>
                      )}
                      
                      {user.status === 'approved' && user.role !== 'admin' && (
                        <button 
                          className="btn btn-info"
                          onClick={() => handlePromote(user.id)}
                          disabled={loading}
                        >
                          <i className="bi bi-arrow-up"></i> Make Admin
                        </button>
                      )}
                      
                      {user.role === 'admin' && user.id !== 1 && (
                        <button 
                          className="btn btn-secondary"
                          onClick={() => handleDemote(user.id)}
                          disabled={loading}
                        >
                          <i className="bi bi-arrow-down"></i> Remove Admin
                        </button>
                      )}
                      
                      {/* Don't allow deleting self or user ID 1 (initial admin) */}
                      {user.id !== 1 && (
                        <button 
                          className="btn btn-danger ms-1"
                          onClick={() => handleDelete(user.id)}
                          disabled={loading}
                          title="Delete user"
                        >
                          <i className="bi bi-trash"></i> Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;